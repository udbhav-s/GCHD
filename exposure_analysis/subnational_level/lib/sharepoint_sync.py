# sharepoint_sync.py
#
# Automates the Google Drive -> SharePoint hand-off for the per-country raster
# exports produced by 04_adm2_hazard_exposure_raster_country.ipynb.
#
# Pipeline (all delegated / interactive auth, no service account):
#   Stage 0  ensure_drive_folder       pre-create the root-level <ucode> Drive
#                                       folder so concurrent EE exports don't
#                                       race and spawn duplicate same-name folders.
#   Stage B  wait_for_tasks            block until every EE export task finishes.
#   Stage C1 download_drive_files      pull the finished GeoTIFFs from Drive.
#   Stage C2 sync_to_sharepoint        push them into
#                                       .../2025/<Country Name>/rasters/ on SharePoint,
#                                       creating the folders if missing.
#   Stage D                            (caller) delete local temp; Drive kept as backup.
#
# Auth model
# ----------
# - Google Drive: delegated OAuth (InstalledAppFlow). First run opens a browser
#   consent for the user's own Google account (the same one EE exports to) and
#   caches a token locally.
# - SharePoint: Microsoft Graph via MSAL device-code flow. Prints a code + URL
#   the user enters in a browser ONLINE. Re-auth happens every run
#   unless MSAL's token cache is persisted.
#
# Dependencies:
#   pip install google-api-python-client google-auth-oauthlib msal requests
#
# Security: never commit the cached Drive token or any client_secret. Keep them
# under credentials/ (gitignored) like the existing GEE service account.

from __future__ import annotations

import io
import os
import time
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import requests

# ---------------------------------------------------------------------------
# ucode -> country name
# ---------------------------------------------------------------------------

def load_ucode_to_name(countries_info_csv: str | Path) -> Dict[str, str]:
    """Build a {ucode: name} map from config/countries_info.csv.

    The SharePoint per-country folders are named by the human-readable country
    `name` (e.g. 'American Samoa (USA)'), while the pipeline keys everything by
    `ucode` (e.g. 'ASM_V1'). This bridges the two.
    """
    import pandas as pd

    df = pd.read_csv(countries_info_csv)
    missing = {"ucode", "name"} - set(df.columns)
    if missing:
        raise ValueError(f"countries_info.csv missing columns: {missing}")
    return dict(zip(df["ucode"].astype(str), df["name"].astype(str)))


# ===========================================================================
# Google Drive
# ===========================================================================

DRIVE_SCOPES = ["https://www.googleapis.com/auth/drive"]
_FOLDER_MIME = "application/vnd.google-apps.folder"


def get_drive_service(
    client_secret_file: str | Path,
    token_file: str | Path = "credentials/drive_token.json",
):
    """Return an authorized Google Drive v3 service via delegated OAuth.

    `client_secret_file` is an OAuth *desktop app* client downloaded from the
    Google Cloud console. The resulting user token is cached at `token_file`
    so subsequent runs don't re-prompt. Both files must stay gitignored.

    Scope is full `drive` (not readonly) because Stage 0 needs to *create*
    folders before the EE exports run.
    """
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build

    token_file = Path(token_file)
    creds = None
    if token_file.exists():
        creds = Credentials.from_authorized_user_file(str(token_file), DRIVE_SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                str(client_secret_file), DRIVE_SCOPES
            )
            creds = flow.run_local_server(port=0)
        token_file.parent.mkdir(parents=True, exist_ok=True)
        token_file.write_text(creds.to_json())

    return build("drive", "v3", credentials=creds, cache_discovery=False)


def ensure_drive_folder(service, ucode: str) -> str:
    """Stage 0 — find-or-create the root-level Drive folder named `ucode`.

    Returns the folder id. Behaviour:
      - exactly one match -> reuse its id
      - several matches    -> warn, reuse the first (a previous race already
                              created duplicates; don't make it worse)
      - none               -> create it

    Creating the canonical folder *before* EE exports start means EE's lazy
    by-name folder creation finds an existing folder instead of racing to make
    duplicates when many export tasks fire at once.

    NOTE: EE's Export `folder=` argument matches by *name*, not id. This
    guarantees a single folder with that name exists; it does not let EE target
    a specific id. If duplicates already exist, resolve them in Drive once.
    """
    q = (
        f"mimeType = '{_FOLDER_MIME}' and name = '{ucode}' "
        "and 'root' in parents and trashed = false"
    )
    resp = service.files().list(
        q=q, spaces="drive", fields="files(id, name)", pageSize=10
    ).execute()
    folders = resp.get("files", [])

    if len(folders) == 1:
        return folders[0]["id"]
    if len(folders) > 1:
        print(
            f"⚠️  {len(folders)} Drive folders named '{ucode}' already exist; "
            f"reusing the first ({folders[0]['id']}). Consider de-duplicating."
        )
        return folders[0]["id"]

    meta = {"name": ucode, "mimeType": _FOLDER_MIME, "parents": ["root"]}
    created = service.files().create(body=meta, fields="id").execute()
    print(f"📁 Created Drive folder '{ucode}' ({created['id']}).")
    return created["id"]


def download_drive_files(
    service,
    filenames: Iterable[str],
    dest_dir: str | Path,
    parent_folder_id: Optional[str] = None,
) -> List[Path]:
    """Stage C1 — download the named TIFFs from Drive into `dest_dir`.

    `filenames` are EE export descriptions WITHOUT extension (the
    `fileNamePrefix`); EE writes `<description>.tif`. Pass `parent_folder_id`
    to scope the search to one country's folder (recommended — avoids picking
    up a same-named file elsewhere in Drive).

    Returns the list of local Paths actually downloaded. Missing files are
    warned about and skipped.
    """
    from googleapiclient.http import MediaIoBaseDownload

    dest_dir = Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    downloaded: List[Path] = []

    for name in filenames:
        fname = name if name.lower().endswith(".tif") else f"{name}.tif"
        q = f"name = '{fname}' and trashed = false"
        if parent_folder_id:
            q += f" and '{parent_folder_id}' in parents"

        resp = service.files().list(
            q=q, spaces="drive", fields="files(id, name, size)", pageSize=10
        ).execute()
        files = resp.get("files", [])
        if not files:
            print(f"⚠️  Drive file not found, skipping: {fname}")
            continue
        if len(files) > 1:
            print(f"⚠️  {len(files)} Drive files named '{fname}'; using the first.")

        file_id = files[0]["id"]
        out_path = dest_dir / fname
        request = service.files().get_media(fileId=file_id)
        with io.FileIO(out_path, "wb") as fh:
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()
        downloaded.append(out_path)
        print(f"⬇️  Downloaded {fname}")

    return downloaded


# ===========================================================================
# Earth Engine task waiting (Stage B)
# ===========================================================================

_TERMINAL = {"COMPLETED", "FAILED", "CANCELLED", "CANCEL_REQUESTED"}


def wait_for_tasks(
    tasks: List,
    poll_seconds: int = 30,
    max_wait_seconds: Optional[int] = None,
) -> Tuple[List[str], List[Tuple[str, str]]]:
    """Stage B — block until every started EE task reaches a terminal state.

    `tasks` is a list of started `ee.batch.Task` objects (collect them by
    passing `return_task=True` to the export helpers). Polls every
    `poll_seconds`, printing a compact status line.

    Returns (completed_descriptions, failures) where `failures` is a list of
    (description, error_message). `COMPLETED` descriptions feed Stage C1's
    download.
    """
    start = time.time()
    completed: List[str] = []
    failures: List[Tuple[str, str]] = []
    pending = list(tasks)

    while pending:
        still_pending = []
        counts = {"READY": 0, "RUNNING": 0, "COMPLETED": 0, "FAILED": 0, "OTHER": 0}
        for task in pending:
            status = task.status()
            state = status.get("state", "UNKNOWN")
            desc = status.get("description", "<no-desc>")
            if state in _TERMINAL:
                if state == "COMPLETED":
                    completed.append(desc)
                    counts["COMPLETED"] += 1
                else:
                    failures.append((desc, status.get("error_message", state)))
                    counts["FAILED"] += 1
            else:
                still_pending.append(task)
                counts[state if state in counts else "OTHER"] += 1

        print(
            f"[{time.strftime('%H:%M:%S')}] "
            f"ready={counts['READY']} running={counts['RUNNING']} "
            f"done={len(completed)} failed={len(failures)} "
            f"pending={len(still_pending)}"
        )

        pending = still_pending
        if not pending:
            break
        if max_wait_seconds is not None and (time.time() - start) > max_wait_seconds:
            print(f"⏱️  Timed out after {max_wait_seconds}s with {len(pending)} still pending.")
            break
        time.sleep(poll_seconds)

    if failures:
        print(f"❌ {len(failures)} task(s) failed:")
        for desc, msg in failures:
            print(f"   - {desc}: {msg}")
    print(f"✅ {len(completed)} task(s) completed.")
    return completed, failures


# ===========================================================================
# SharePoint via Microsoft Graph (Stage C2)
# ===========================================================================

GRAPH_ROOT = "https://graph.microsoft.com/v1.0"
GRAPH_SCOPES = ["Sites.ReadWrite.All"]
_UPLOAD_CHUNK = 8 * 1024 * 1024  # 8 MiB; must be a multiple of 320 KiB per Graph


def graph_device_code_token(client_id: str, tenant_id: str) -> str:
    """Acquire a Graph access token via MSAL device-code flow (delegated).

    Prints a URL + code for the user to enter in a browser online. Returns the
    bearer access token string. Re-run each session unless you persist MSAL's
    token cache.
    """
    import msal

    authority = f"https://login.microsoftonline.com/{tenant_id}"
    app = msal.PublicClientApplication(client_id, authority=authority)

    # Try silent first (in case a cached account exists this process).
    accounts = app.get_accounts()
    if accounts:
        result = app.acquire_token_silent(GRAPH_SCOPES, account=accounts[0])
        if result and "access_token" in result:
            return result["access_token"]

    flow = app.initiate_device_flow(scopes=GRAPH_SCOPES)
    if "user_code" not in flow:
        raise RuntimeError(f"Failed to start device flow: {flow.get('error_description', flow)}")

    # Make the login instructions impossible to miss and flush them immediately —
    # Jupyter can otherwise buffer this until the (blocking) call below returns,
    # which makes the cell look like it's hanging with nothing to act on.
    print("\n" + "=" * 70, flush=True)
    print("ACTION REQUIRED — SharePoint device-code login", flush=True)
    print(f"  1. Open:  {flow.get('verification_uri', 'https://microsoft.com/devicelogin')}", flush=True)
    print(f"  2. Enter code:  {flow['user_code']}", flush=True)
    print("  3. Sign in with your UNICEF account + Authenticator.", flush=True)
    print("This cell will keep running until you finish (or the code expires).", flush=True)
    print("=" * 70 + "\n", flush=True)

    result = app.acquire_token_by_device_flow(flow)  # blocks until the user completes login
    if "access_token" not in result:
        raise RuntimeError(
            f"Auth failed: {result.get('error')}: {result.get('error_description')}"
        )
    return result["access_token"]


def _headers(token: str) -> Dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def resolve_site_drive(
    token: str,
    hostname: str,
    site_path: str,
    library_name: str,
) -> Tuple[str, str]:
    """Resolve (site_id, drive_id) for a named document library.

    e.g. hostname='unicef.sharepoint.com', site_path='teams/DAPM',
    library_name='DocumentLibrary4'.
    """
    site_url = f"{GRAPH_ROOT}/sites/{hostname}:/{site_path.strip('/')}"
    r = requests.get(site_url, headers=_headers(token))
    r.raise_for_status()
    site_id = r.json()["id"]

    r = requests.get(f"{GRAPH_ROOT}/sites/{site_id}/drives", headers=_headers(token))
    r.raise_for_status()
    drives = r.json().get("value", [])
    for d in drives:
        if d.get("name") == library_name:
            return site_id, d["id"]
    available = [d.get("name") for d in drives]
    raise ValueError(
        f"Document library '{library_name}' not found on site {site_path}. "
        f"Available: {available}"
    )


def ensure_sp_folder_path(token: str, drive_id: str, folder_path: str) -> str:
    """Find-or-create each segment of `folder_path` under the drive root.

    Returns the item id of the deepest folder. Used to guarantee
    '<Country Name>/rasters' exists before uploading.
    """
    parent_id = "root"
    accumulated = ""
    for segment in [s for s in folder_path.split("/") if s]:
        accumulated = f"{accumulated}/{segment}" if accumulated else segment
        # Does it already exist?
        get_url = f"{GRAPH_ROOT}/drives/{drive_id}/root:/{accumulated}"
        r = requests.get(get_url, headers=_headers(token))
        if r.status_code == 200:
            parent_id = r.json()["id"]
            continue
        if r.status_code != 404:
            r.raise_for_status()
        # Create it under the current parent.
        create_url = f"{GRAPH_ROOT}/drives/{drive_id}/items/{parent_id}/children"
        body = {
            "name": segment,
            "folder": {},
            "@microsoft.graph.conflictBehavior": "fail",
        }
        cr = requests.post(create_url, headers=_headers(token), json=body)
        if cr.status_code == 409:  # created by a concurrent caller; re-fetch
            r2 = requests.get(get_url, headers=_headers(token))
            r2.raise_for_status()
            parent_id = r2.json()["id"]
        else:
            cr.raise_for_status()
            parent_id = cr.json()["id"]
            print(f"Created SharePoint folder: {accumulated}")
    return parent_id


def upload_large_file(
    token: str,
    drive_id: str,
    dest_folder_path: str,
    local_path: str | Path,
    chunk_size: int = _UPLOAD_CHUNK,
) -> dict:
    """Upload one file via a resumable upload session (handles >4 MB TIFFs).

    Creates an upload session at
    /drives/{drive_id}/root:/{dest_folder_path}/{filename}:/createUploadSession
    then PUTs the file in `chunk_size` ranges. Returns the created driveItem.
    """
    local_path = Path(local_path)
    file_size = local_path.stat().st_size
    item_path = f"{dest_folder_path.strip('/')}/{local_path.name}"

    session_url = f"{GRAPH_ROOT}/drives/{drive_id}/root:/{item_path}:/createUploadSession"
    body = {"item": {"@microsoft.graph.conflictBehavior": "replace"}}
    r = requests.post(session_url, headers=_headers(token), json=body)
    r.raise_for_status()
    upload_url = r.json()["uploadUrl"]

    with open(local_path, "rb") as fh:
        start = 0
        response = None
        while start < file_size:
            chunk = fh.read(chunk_size)
            end = start + len(chunk) - 1
            headers = {
                "Content-Length": str(len(chunk)),
                "Content-Range": f"bytes {start}-{end}/{file_size}",
            }
            response = requests.put(upload_url, headers=headers, data=chunk)
            if response.status_code not in (200, 201, 202):
                response.raise_for_status()
            start = end + 1

    print(f"Uploaded {local_path.name} -> {dest_folder_path}")
    return response.json() if response is not None else {}


def sync_to_sharepoint(
    token: str,
    drive_id: str,
    sp_base_path: str,
    country_name: str,
    local_files: Iterable[str | Path],
    rasters_subfolder: str = "rasters",
    delete_local_after: bool = True,
) -> List[Path]:
    """Stage C2+D — upload a country's TIFFs to
    `{sp_base_path}/{country_name}/{rasters_subfolder}/`, creating folders as
    needed, then optionally delete each local copy after a confirmed upload.

    Returns the list of local files that were deleted.
    """
    dest_path = f"{sp_base_path.strip('/')}/{country_name}/{rasters_subfolder}"
    ensure_sp_folder_path(token, drive_id, dest_path)

    deleted: List[Path] = []
    for f in local_files:
        f = Path(f)
        upload_large_file(token, drive_id, dest_path, f)
        if delete_local_after:
            f.unlink(missing_ok=True)
            deleted.append(f)
    return deleted
