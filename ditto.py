import flet as ft
import json
from datetime import datetime, timedelta

API_BASE_URL = "https://short-url.leapcell.app"
TOKEN_REFRESH_TIME = 8

class SessionData:
    def __init__(self):
        self.access_token = None
        self.current_alias = None
        self.token_time = None


# Ditto Pokemon image
ditto_image = ft.Image(
    src="https://ik.imagekit.io/2zdmk9mex/uploads/avatar.png?updatedAt=1761076843950",
    width=80,
    height=80,
    fit=ft.ImageFit.CONTAIN,
)

async def refresh_token(page:ft.Page):
    response = await make_request(
        page,
        f"{API_BASE_URL}/refresh_token",
        method="GET",
        auth_token=page.session_data.access_token,
        flag=False
    )
    if response['ok']:
        data = response['body']
        page.session_data.access_token = data.get("access_token")
        page.session_data.token_time=datetime.now()

async def make_request(page: ft.Page, url, method="GET", data=None, timeout=10, auth_token=None,flag=True):
    """
    HTTP request that works in both desktop and web builds
    """
    if flag and page.session_data.token_time and (datetime.now()-page.session_data.token_time).total_seconds()/60 > TOKEN_REFRESH_TIME:
        await refresh_token(page)
    try:
        import sys
        if 'pyodide' in sys.modules:
            # Running in browser - use JavaScript fetch
            return await make_request_js(page, url, method, data, auth_token)
        else:
            # Running in desktop - use urllib
            return make_request_urllib(url, method, data, timeout, auth_token)
    except Exception as e:
        return {
            'ok': False,
            'status': 0,
            'body': {'detail': f'Error: {str(e)}'}
        }


async def make_request_js(page: ft.Page, url, method="GET", data=None, auth_token=None):
    """Use JavaScript fetch for browser environment"""
    import js
    from pyodide.ffi import to_js, JsException

    headers = {'Content-Type': 'application/json'}

    if auth_token:
        headers['Authorization'] = f'Bearer {auth_token}'

    options = {
        'method': method,
        'headers': headers
    }

    if data:
        options['body'] = json.dumps(data)

    try:
        # Await the fetch promise
        response = await js.fetch(url, to_js(options))

        # Await the text promise
        body_text = await response.text()

        return {
            'ok': response.ok,
            'status': response.status,
            'body': json.loads(body_text) if body_text else {}
        }
    except JsException as e:
        return {
            'ok': False,
            'status': 0,
            'body': {'detail': f'JS Fetch error: {str(e)}'}
        }
    except Exception as e:
        return {
            'ok': False,
            'status': 0,
            'body': {'detail': f'Error: {str(e)}'}
        }


def make_request_urllib(url, method="GET", data=None, timeout=10, auth_token=None):
    """Original urllib implementation for desktop"""
    import urllib.request
    import urllib.error

    try:
        headers = {'Content-Type': 'application/json'} if data else {}

        if auth_token:
            headers['Authorization'] = f'Bearer {auth_token}'

        if data:
            data = json.dumps(data).encode('utf-8')

        req = urllib.request.Request(
            url,
            data=data,
            headers=headers,
            method=method
        )

        with urllib.request.urlopen(req, timeout=timeout) as response:
            body = response.read().decode('utf-8')
            return {
                'ok': 200 <= response.status < 300,
                'status': response.status,
                'body': json.loads(body) if body else {}
            }
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8')
        return {
            'ok': False,
            'status': e.code,
            'body': json.loads(body) if body else {'detail': str(e)}
        }
    except Exception as e:
        return {
            'ok': False,
            'status': 0,
            'body': {'detail': f'Error: {str(e)}'}
        }


async def show_manage_alias_page(page: ft.Page):
    is_editing = False
    is_editing_password = False
    alias_data = {}

    def go_back(e):
        page.controls.clear()
        show_main_page(page)
        page.update()

    back_button = ft.TextButton(
        text="← Back to Home",
        style=ft.ButtonStyle(
            color="#5ab896",
        ),
        on_click=go_back,
    )

    title_row = ft.Row(
        [
            ditto_image,
            ft.Text(
                f"Manage Alias: {page.session_data.current_alias}",
                size=28,
                weight=ft.FontWeight.W_400,
                color="#5ab896",
            ),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=10,
    )

    async def on_refresh_click(e):
        status_text.value = "Refreshing..."
        status_text.color = "#5ab896"
        page.update()
        await load_alias_details()
        status_text.value = "Data refreshed successfully!"
        page.update()

    def on_logout_click(e):
        page.session_data = SessionData()
        page.controls.clear()
        show_login_page(page)
        page.update()

    refresh_button = ft.ElevatedButton(
        content=ft.Row(
            [
                ft.Icon(ft.Icons.REFRESH, size=18),
                ft.Text("Refresh", size=14),
            ],
            spacing=8,
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        width=150,
        height=40,
        bgcolor="#4a9b7f",
        color="#ffffff",
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=8),
        ),
        on_click=on_refresh_click,
    )

    logout_button = ft.ElevatedButton(
        content=ft.Row(
            [
                ft.Icon(ft.Icons.LOGOUT, size=18),
                ft.Text("Logout", size=14),
            ],
            spacing=8,
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        width=150,
        height=40,
        bgcolor="#ff6b6b",
        color="#ffffff",
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=8),
        ),
        on_click=on_logout_click,
    )

    action_buttons_row = ft.Row(
        [refresh_button, logout_button],
        spacing=15,
        alignment=ft.MainAxisAlignment.CENTER,
    )

    status_text = ft.Text(
        "",
        color="#ff6b6b",
        size=14,
        text_align=ft.TextAlign.CENTER,
    )

    # Display container for URL info
    url_display_text = ft.Text(
        "Loading...",
        color="#ffffff",
        size=14,
        weight=ft.FontWeight.W_400,
        selectable=True,
    )

    hits_text = ft.Text(
        "",
        color="#8a8a8a",
        size=12,
    )

    created_text = ft.Text(
        "",
        color="#8a8a8a",
        size=12,
    )

    state_text = ft.Text(
        "",
        color="#5ab896",
        size=12,
    )

    def toggle_edit_mode(e):
        nonlocal is_editing
        is_editing = not is_editing

        if is_editing:
            url_display_row.visible = False
            url_edit_row.visible = True
            new_url_field.value = alias_data.get("url", "")
        else:
            url_display_row.visible = True
            url_edit_row.visible = False
            status_text.value = ""

        page.update()

    def toggle_password_edit(e):
        nonlocal is_editing_password
        is_editing_password = not is_editing_password

        if is_editing_password:
            password_edit_container.visible = True
        else:
            password_edit_container.visible = False
            old_password_field.value = ""
            new_password_field.value = ""
            confirm_password_field.value = ""
            status_text.value = ""

        page.update()

    # Fields for updating alias
    new_url_field = ft.TextField(
        label="Target URL",
        border_color="#4a9b7f",
        focused_border_color="#5ab896",
        label_style=ft.TextStyle(color="#8a8a8a"),
        text_style=ft.TextStyle(color="#ffffff"),
        cursor_color="#5ab896",
        width=420,
    )

    edit_button = ft.IconButton(
        icon=ft.Icons.EDIT,
        icon_color="#5ab896",
        tooltip="Edit URL",
        on_click=toggle_edit_mode,
    )

    url_display_row = ft.Row(
        [
            ft.Container(
                content=url_display_text,
                padding=15,
                bgcolor="#2a2a2a",
                border_radius=8,
                border=ft.border.all(1, "#3a3a3a"),
                expand=True,
            ),
            edit_button,
        ],
        spacing=10,
    )

    async def on_update_url_click(e):
        if not new_url_field.value:
            status_text.value = "Please enter a target URL"
            status_text.color = "#ff6b6b"
            page.update()
            return
        status_text.value = "Updating URL..."
        status_text.color = "#5ab896"
        page.update()
        try:
            response = await make_request(
                page,
                f"{API_BASE_URL}/change_url?url={new_url_field.value}",
                method="PATCH",
                auth_token=page.session_data.access_token
            )

            if response['ok']:
                status_text.value = "URL updated successfully!"
                status_text.color = "#5ab896"

                # Reload details
                await load_alias_details()
                toggle_edit_mode(None)
            else:
                error_detail = response['body'].get("detail", "Update failed")
                status_text.value = error_detail
                status_text.color = "#ff6b6b"
            page.update()

        except Exception as ex:
            status_text.value = f"Error: {str(ex)}"
            status_text.color = "#ff6b6b"
            page.update()

    def on_cancel_edit(e):
        toggle_edit_mode(e)

    save_url_button = ft.IconButton(
        icon=ft.Icons.CHECK,
        icon_color="#5ab896",
        tooltip="Save URL",
        on_click=on_update_url_click,
    )

    cancel_url_button = ft.IconButton(
        icon=ft.Icons.CLOSE,
        icon_color="#ff6b6b",
        tooltip="Cancel",
        on_click=on_cancel_edit,
    )

    url_edit_row = ft.Row(
        [
            new_url_field,
            save_url_button,
            cancel_url_button,
        ],
        spacing=5,
        visible=False,
    )

    async def on_reset_hits_click(e):
        # Confirmation dialog
        async def confirm_reset(confirm_e):
            dialog.open = False
            page.update()

            try:
                response = await make_request(
                    page,
                    f"{API_BASE_URL}/reset_hits",
                    method="PATCH",
                    auth_token=page.session_data.access_token
                )

                if response['ok']:
                    status_text.value = "Hits reset successfully!"
                    status_text.color = "#5ab896"
                    await load_alias_details()
                else:
                    error_detail = response['body'].get("detail", "Reset failed")
                    status_text.value = error_detail
                    status_text.color = "#ff6b6b"
                page.update()

            except Exception as ex:
                status_text.value = f"Error: {str(ex)}"
                status_text.color = "#ff6b6b"
                page.update()

        def cancel_reset(cancel_e):
            dialog.open = False
            page.update()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Confirm Reset Hits"),
            content=ft.Text(f"Are you sure you want to reset the hit counter for '{page.session_data.current_alias}'?"),
            actions=[
                ft.TextButton("Cancel", on_click=cancel_reset),
                ft.TextButton("Reset", on_click=confirm_reset, style=ft.ButtonStyle(color="#ff6b6b")),
            ],
        )

        page.overlay.append(dialog)
        dialog.open = True
        page.update()

    async def on_toggle_status_click(e):
        try:
            is_active = alias_data.get("url_state", False)
            if is_active:
                endpoint = "pause"
                status_text.value = "Pausing..."
            else:
                endpoint = "resume"
                status_text.value = "Resuming..."

            status_text.color = "#5ab896"
            page.update()
            response = await make_request(
                page,
                f"{API_BASE_URL}/{endpoint}",
                method="PATCH",
                auth_token=page.session_data.access_token
            )

            if response['ok']:
                action = "paused" if is_active else "resumed"
                status_text.value = f"Alias {action} successfully!"
                status_text.color = "#5ab896"
                await load_alias_details()
            else:
                error_detail = response['body'].get("detail", "Operation failed")
                status_text.value = error_detail
                status_text.color = "#ff6b6b"
            page.update()

        except Exception as ex:
            status_text.value = f"Error: {str(ex)}"
            status_text.color = "#ff6b6b"
            page.update()

    # Reset hits icon button
    reset_hits_icon_button = ft.IconButton(
        icon=ft.Icons.REFRESH,
        icon_color="#4a9b7f",
        tooltip="Reset Hits",
        on_click=on_reset_hits_click,
    )

    # Toggle status icon button
    toggle_status_icon_button = ft.IconButton(
        icon=ft.Icons.PAUSE_CIRCLE,
        icon_color="#ff8c42",
        tooltip="Pause Alias",
        on_click=on_toggle_status_click,
    )

    info_display_container = ft.Container(
        content=ft.Column(
            [
                ft.Text("URL:", color="#8a8a8a", size=14, weight=ft.FontWeight.W_500),
                url_display_row,
                url_edit_row,
                ft.Container(height=10),
                ft.Row(
                    [
                        ft.Icon(ft.Icons.VISIBILITY, size=16, color="#8a8a8a"),
                        hits_text,
                        reset_hits_icon_button,
                    ],
                    spacing=8,
                ),
                ft.Row(
                    [
                        ft.Icon(ft.Icons.CALENDAR_TODAY, size=16, color="#8a8a8a"),
                        created_text,
                    ],
                    spacing=8,
                ),
                ft.Row(
                    [
                        ft.Icon(ft.Icons.CHECK_CIRCLE, size=16, color="#8a8a8a"),
                        state_text,
                        toggle_status_icon_button,
                    ],
                    spacing=8,
                ),
            ],
            spacing=10,
        ),
        width=500,
        padding=20,
        border_radius=12,
        border=ft.border.all(1, "#3a3a3a"),
    )

    # Password edit fields
    old_password_field = ft.TextField(
        label="Old Password",
        password=True,
        can_reveal_password=True,
        border_color="#4a9b7f",
        focused_border_color="#5ab896",
        label_style=ft.TextStyle(color="#8a8a8a"),
        text_style=ft.TextStyle(color="#ffffff"),
        cursor_color="#5ab896",
        width=500,
    )

    new_password_field = ft.TextField(
        label="New Password",
        password=True,
        can_reveal_password=True,
        border_color="#4a9b7f",
        focused_border_color="#5ab896",
        label_style=ft.TextStyle(color="#8a8a8a"),
        text_style=ft.TextStyle(color="#ffffff"),
        cursor_color="#5ab896",
        width=500,
    )

    confirm_password_field = ft.TextField(
        label="Confirm New Password",
        password=True,
        can_reveal_password=True,
        border_color="#4a9b7f",
        focused_border_color="#5ab896",
        label_style=ft.TextStyle(color="#8a8a8a"),
        text_style=ft.TextStyle(color="#ffffff"),
        cursor_color="#5ab896",
        width=500,
    )

    async def on_update_password_click(e):
        if not old_password_field.value or not new_password_field.value or not confirm_password_field.value:
            status_text.value = "Please fill in all password fields"
            status_text.color = "#ff6b6b"
            page.update()
            return

        if new_password_field.value != confirm_password_field.value:
            status_text.value = "New passwords do not match"
            status_text.color = "#ff6b6b"
            page.update()
            return

        try:
            update_data = {
                'url_code': page.session_data.current_alias,
                'old_url_pass': old_password_field.value,
                'new_url_pass': new_password_field.value
            }

            response = await make_request(
                page,
                f"{API_BASE_URL}/change_password",
                method="POST",
                data=update_data,
                auth_token=page.session_data.access_token
            )

            if response['ok']:
                status_text.value = "Password updated successfully!"
                status_text.color = "#5ab896"
                old_password_field.value = ""
                new_password_field.value = ""
                confirm_password_field.value = ""
                toggle_password_edit(None)
            else:
                error_detail = response['body'].get("detail", "Update failed")
                status_text.value = error_detail
                status_text.color = "#ff6b6b"
            page.update()

        except Exception as ex:
            status_text.value = f"Error: {str(ex)}"
            status_text.color = "#ff6b6b"
            page.update()

    def on_cancel_password_edit(e):
        toggle_password_edit(e)

    save_password_button = ft.ElevatedButton(
        text="Save Password",
        width=200,
        height=45,
        bgcolor="#5ab896",
        color="#ffffff",
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=8),
        ),
        on_click=on_update_password_click,
    )

    cancel_password_button = ft.ElevatedButton(
        text="Cancel",
        width=200,
        height=45,
        bgcolor="#3a3a3a",
        color="#ffffff",
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=8),
        ),
        on_click=on_cancel_password_edit,
    )

    password_edit_container = ft.Container(
        content=ft.Column(
            [
                ft.Text(
                    "Change Password",
                    size=18,
                    weight=ft.FontWeight.W_500,
                    color="#5ab896",
                ),
                ft.Container(height=10),
                old_password_field,
                ft.Container(height=15),
                new_password_field,
                ft.Container(height=15),
                confirm_password_field,
                ft.Container(height=20),
                ft.Row(
                    [save_password_button, cancel_password_button],
                    spacing=20,
                    alignment=ft.MainAxisAlignment.CENTER,
                    wrap=True,
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        visible=False,
        padding=20,
        border_radius=12,
        border=ft.border.all(1, "#3a3a3a"),
        width=500,
    )

    # Fetch current alias details
    async def load_alias_details():
        nonlocal alias_data
        try:
            response = await make_request(
                page,
                f"{API_BASE_URL}/details",
                method="GET",
                auth_token=page.session_data.access_token
            )

            if response['ok']:
                data = response['body'].get("data", {})
                alias_data = data

                url_display_text.value = data.get("url", "N/A")
                hits_text.value = f"Hits: {data.get('url_hits', 0)}"

                created_at = data.get("url_created_at", "")
                if created_at:
                    # Format the date
                    from datetime import datetime
                    try:
                        dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        created_text.value = f"Created: {dt.strftime('%b %d, %Y at %I:%M %p')}"
                    except:
                        created_text.value = f"Created: {created_at}"

                is_active = data.get("url_state", False)
                state_text.value = f"Status: {'Active' if is_active else 'Paused'}"
                state_text.color = "#5ab896" if is_active else "#ff6b6b"

                # Update toggle button icon and tooltip
                toggle_status_icon_button.icon = ft.Icons.PAUSE_CIRCLE if is_active else ft.Icons.PLAY_CIRCLE
                toggle_status_icon_button.icon_color = "#ff8c42" if is_active else "#5ab896"
                toggle_status_icon_button.tooltip = "Pause Alias" if is_active else "Resume Alias"
            else:
                url_display_text.value = "Failed to load alias details"
                url_display_text.color = "#ff6b6b"
            page.update()
        except Exception as ex:
            url_display_text.value = f"Error: {str(ex)}"
            url_display_text.color = "#ff6b6b"
            page.update()

    async def on_delete_click(e):
        # Confirmation dialog
        async def confirm_delete(confirm_e):
            dialog.open = False
            page.update()

            try:
                response = await make_request(
                    page,
                    f"{API_BASE_URL}/delete",
                    method="DELETE",
                    auth_token=page.session_data.access_token
                )

                if response['ok']:
                    status_text.value = "Alias deleted successfully!"
                    status_text.color = "#5ab896"
                    page.update()

                    # Return to main page after short delay
                    import asyncio
                    await asyncio.sleep(1.5)
                    page.controls.clear()
                    show_main_page(page)
                    page.update()
                else:
                    error_detail = response['body'].get("detail", "Delete failed")
                    status_text.value = error_detail
                    status_text.color = "#ff6b6b"
                    page.update()

            except Exception as ex:
                status_text.value = f"Error: {str(ex)}"
                status_text.color = "#ff6b6b"
                page.update()

        def cancel_delete(cancel_e):
            dialog.open = False
            page.update()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Confirm Delete"),
            content=ft.Text(f"Are you sure you want to delete the alias '{page.session_data.current_alias}'? This action cannot be undone."),
            actions=[
                ft.TextButton("Cancel", on_click=cancel_delete),
                ft.TextButton("Delete", on_click=confirm_delete, style=ft.ButtonStyle(color="#ff6b6b")),
            ],
        )

        page.overlay.append(dialog)
        dialog.open = True
        page.update()

    edit_password_button = ft.ElevatedButton(
        content=ft.Row(
            [
                ft.Icon(ft.Icons.LOCK, size=20),
                ft.Text("Edit Password", size=14),
            ],
            spacing=8,
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        width=240,
        height=50,
        bgcolor="#ff8c42",
        color="#ffffff",
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=8),
        ),
        on_click=toggle_password_edit,
    )

    delete_button = ft.ElevatedButton(
        content=ft.Row(
            [
                ft.Icon(ft.Icons.DELETE_FOREVER, size=20),
                ft.Text("Delete Alias", size=14),
            ],
            spacing=8,
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        width=240,
        height=50,
        bgcolor="#ff6b6b",
        color="#ffffff",
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=8),
        ),
        on_click=on_delete_click,
    )

    page.add(
        ft.Container(
            content=ft.Column(
                [
                    back_button,
                    ft.Container(height=20),
                    title_row,
                    ft.Container(height=20),
                    ft.Divider(color="#333333", height=1),
                    ft.Container(height=15),
                    action_buttons_row,
                    ft.Container(height=15),
                    info_display_container,
                    ft.Container(height=10),
                    status_text,
                    ft.Container(height=20),
                    password_edit_container,
                    ft.Container(height=30),
                    ft.Divider(color="#333333", height=1),
                    ft.Container(height=20),
                    ft.Text(
                        "Danger Zone",
                        size=18,
                        weight=ft.FontWeight.W_500,
                        color="#ff6b6b",
                    ),
                    ft.Container(height=10),
                    ft.Row(
                        [edit_password_button, delete_button],
                        spacing=20,
                        alignment=ft.MainAxisAlignment.CENTER,
                        wrap=True,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=40,
        )
    )

    # Load alias details after page is rendered
    await load_alias_details()




def show_login_page(page: ft.Page):
    def go_back(e):
        page.controls.clear()
        show_main_page(page)
        page.update()

    back_button = ft.TextButton(
        text="← Back to Create Alias",
        style=ft.ButtonStyle(
            color="#5ab896",
        ),
        on_click=go_back,
    )

    login_title = ft.Row(
        [
            ditto_image,
            ft.Text(
                "Login to Alias",
                size=28,
                weight=ft.FontWeight.W_400,
                color="#5ab896",
            ),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=10,
    )

    alias_field = ft.TextField(
        label="Enter Alias to Manage",
        border_color="#4a9b7f",
        focused_border_color="#5ab896",
        label_style=ft.TextStyle(color="#8a8a8a"),
        text_style=ft.TextStyle(color="#ffffff"),
        cursor_color="#5ab896",
        width=500,
    )

    password_field = ft.TextField(
        label="Password",
        password=True,
        can_reveal_password=True,
        border_color="#4a9b7f",
        focused_border_color="#5ab896",
        label_style=ft.TextStyle(color="#8a8a8a"),
        text_style=ft.TextStyle(color="#ffffff"),
        cursor_color="#5ab896",
        width=500,
    )

    status_text = ft.Text(
        "",
        color="#ff6b6b",
        size=14,
        text_align=ft.TextAlign.CENTER,
    )

    async def on_login_click(e):
        if not alias_field.value or not password_field.value:
            status_text.value = "Please fill in both fields"
            status_text.color = "#ff6b6b"
            page.update()
            return
        status_text.value = "Loging in..."
        status_text.color = "#5ab896"
        page.update()
        try:
            response = await make_request(
                page,
                f"{API_BASE_URL}/login",
                method="POST",
                data={
                    'url_code': alias_field.value,
                    'url_pass': password_field.value
                }
            )

            if response['ok']:
                data = response['body']
                page.session_data.access_token = data.get("access_token")
                page.session_data.current_alias = alias_field.value
                page.session_data.token_time =datetime.now()

                status_text.value = "Login successful!"
                status_text.color = "#5ab896"
                page.update()

                # Navigate to manage alias page
                page.controls.clear()
                await show_manage_alias_page(page)
                page.update()
            else:
                error_detail = response['body'].get("detail", "Login failed")
                status_text.value = error_detail
                status_text.color = "#ff6b6b"
                page.update()

        except Exception as ex:
            status_text.value = f"Error: {str(ex)}"
            status_text.color = "#ff6b6b"
            page.update()

    login_button = ft.ElevatedButton(
        text="Login",
        width=500,
        height=50,
        bgcolor="#5ab896",
        color="#ffffff",
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=8),
        ),
        on_click=on_login_click,
    )

    page.add(
        ft.Container(
            content=ft.Column(
                [
                    back_button,
                    ft.Container(height=20),
                    login_title,
                    ft.Container(height=20),
                    ft.Divider(color="#333333", height=1),
                    ft.Container(height=20),
                    alias_field,
                    ft.Container(height=20),
                    password_field,
                    ft.Container(height=30),
                    login_button,
                    ft.Container(height=10),
                    status_text,
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=40,
        )
    )


def show_down_page(page: ft.Page):
    title_row = ft.Row(
        [
            ditto_image,
            ft.Text(
                "Ditto - Shrink your URL",
                size=28,
                weight=ft.FontWeight.W_400,
                color="#5ab896",
            ),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=10,
    )

    async def retry_connection(e):
        page.controls.clear()
        await connection(page)
        page.update()

    page.add(
        ft.Column(
            [
                title_row,
                ft.Container(height=20),
                ft.Divider(color="#333333", height=1),
                ft.Container(height=30),
                ft.Icon(name=ft.Icons.ERROR, color="#ff6b6b", size=100),
                ft.Text("Service is currently unavailable", size=24, weight=ft.FontWeight.BOLD),
                ft.Text("Please try again later.", size=18, color="#5a5a5a"),
                ft.ElevatedButton(
                    "Retry",
                    on_click=retry_connection
                )
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            expand=True
        )
    )


def show_main_page(page: ft.Page):
    status_text = ft.Text(
        "",
        color="#ff6b6b",
        size=14,
        text_align=ft.TextAlign.CENTER,
    )

    short_url_text = ft.Text(
        "",
        color="#5ab896",
        size=16,
        weight=ft.FontWeight.W_500,
    )

    def on_url_click(e):
        if short_url_text.data:
            page.launch_url(short_url_text.data)

    def on_copy_click(e):
        if short_url_text.data:
            page.set_clipboard(short_url_text.data)
            copy_button.content.controls[1].value = "Copied!"
            page.update()

    copy_button = ft.Container(
        content=ft.Row(
            [
                ft.Icon(ft.Icons.CONTENT_COPY, color="#ffffff", size=18),
                ft.Text("Copy", color="#ffffff", size=14, weight=ft.FontWeight.W_500),
            ],
            spacing=8,
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        bgcolor="#1b7f5a",
        padding=ft.padding.symmetric(horizontal=16, vertical=10),
        border_radius=6,
        on_click=on_copy_click,
        visible=False,
    )

    short_url_container = ft.Container(
        content=ft.Row(
            [
                ft.TextButton(
                    content=short_url_text,
                    on_click=on_url_click,
                    style=ft.ButtonStyle(
                        padding=0,
                        overlay_color="transparent",
                    ),
                ),
                copy_button,
            ],
            spacing=15,
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        visible=False,
    )

    url_field = ft.TextField(
        label="Long URL",
        border_color="#4a9b7f",
        focused_border_color="#5ab896",
        label_style=ft.TextStyle(color="#8a8a8a"),
        text_style=ft.TextStyle(color="#ffffff"),
        cursor_color="#5ab896",
        width=500,
    )

    alias_field = ft.TextField(
        label="Alias",
        border_color="#4a9b7f",
        focused_border_color="#5ab896",
        label_style=ft.TextStyle(color="#8a8a8a"),
        text_style=ft.TextStyle(color="#ffffff"),
        cursor_color="#5ab896",
        width=500,
    )

    password_field = ft.TextField(
        label="Password",
        password=True,
        can_reveal_password=True,
        border_color="#4a9b7f",
        focused_border_color="#5ab896",
        label_style=ft.TextStyle(color="#8a8a8a"),
        text_style=ft.TextStyle(color="#ffffff"),
        cursor_color="#5ab896",
        width=500,
        hint_text="Leave empty for password-less",
        hint_style=ft.TextStyle(color="#5a5a5a", size=12),
    )

    title_row = ft.Row(
        [
            ditto_image,
            ft.Text(
                "Ditto - Shrink your URL",
                size=28,
                weight=ft.FontWeight.W_400,
                color="#5ab896",
            ),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=10,
    )

    async def on_shrink_click(e):
        if shrink_button.text == "Shrink URL":
            if not url_field.value or not alias_field.value:
                status_text.value = "Please fill in both Long URL and Alias fields"
                status_text.color = "#ff6b6b"
                short_url_container.visible = False
                short_url_text.value = ""
                short_url_text.data = ""
            else:
                status_text.value = "Shrinking..."
                status_text.color = "#5ab896"
                page.update()
                try:
                    response = await make_request(
                        page,
                        f"{API_BASE_URL}/create",
                        method="POST",
                        data={
                            'url': url_field.value,
                            'url_code': alias_field.value,
                            'url_pass': password_field.value
                        }
                    )

                    if response['ok']:
                        data = response['body']
                        short_url = data.get("short_url", "")
                        status_text.value = "URL shortened successfully!"
                        status_text.color = "#5ab896"
                        short_url_text.value = short_url
                        short_url_text.data = short_url
                        short_url_container.visible = True
                        copy_button.visible = True
                        copy_button.content.controls[1].value = "Copy"
                        shrink_button.text = "Shrink another URL"
                    else:
                        status_text.value = response['body'].get("detail", "An error occurred")
                        status_text.color = "#ff6b6b"
                        short_url_container.visible = False
                        short_url_text.value = ""
                        short_url_text.data = ""
                except Exception as ex:
                    status_text.value = f"Error: {str(ex)}"
                    status_text.color = "#ff6b6b"
                    short_url_container.visible = False
                    short_url_text.value = ""
                    short_url_text.data = ""
        else:
            page.controls.clear()
            show_main_page(page)
        page.update()

    shrink_button = ft.ElevatedButton(
        text="Shrink URL",
        width=500,
        height=50,
        bgcolor="#5ab896",
        color="#ffffff",
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=8),
        ),
        on_click=on_shrink_click,
    )

    async def isLogedIn():
        response = await make_request(page, f"{API_BASE_URL}/validate_token", timeout=5, auth_token=page.session_data.access_token)
        return response['ok']

    async def on_link_click(e):
        page.controls.clear()
        if page.session_data.access_token and await isLogedIn():
            await show_manage_alias_page(page)
        else:
            page.session_data = SessionData()
            show_login_page(page)
        page.update()

    manage_alias_text = ft.Row(
        [
            ft.Text(
                "Need to manage to old Alias? Click",
                color="#8a8a8a",
                size=14,
            ),
            ft.TextButton(
                text="here",
                style=ft.ButtonStyle(
                    color="#5ab896",
                    padding=0,
                ),
                on_click=on_link_click,
            ),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
    )

    page.add(
        ft.Container(
            content=ft.Column(
                [
                    title_row,
                    ft.Container(height=20),
                    ft.Divider(color="#333333", height=1),
                    ft.Container(height=30),
                    url_field,
                    ft.Container(height=20),
                    alias_field,
                    ft.Container(height=20),
                    password_field,
                    ft.Container(height=30),
                    shrink_button,
                    ft.Container(height=10),
                    status_text,
                    ft.Container(height=10),
                    short_url_container,
                    ft.Container(height=10),
                    manage_alias_text,
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=40,
        )
    )


async def connection(page: ft.Page):
    status_text = ft.Text(
        "Loading...",
        color="#ff6b6b",
        size=20,
        text_align=ft.TextAlign.CENTER,
    )
    page.add(
        ft.Container(
            content=ft.Column(
                [
                    status_text,
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            padding=40,
            alignment=ft.alignment.center,
        )
    )
    page.update()
    try:
        response = await make_request(page, f"{API_BASE_URL}/health", timeout=10)
        page.controls.clear()
        if response['ok']:
            show_main_page(page)
        else:
            show_down_page(page)
    except Exception:
        show_down_page(page)

async def main(page: ft.Page):
    page.title = "Ditto"
    page.bgcolor = "#1a1a1a"
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.vertical_alignment = ft.MainAxisAlignment.START
    page.padding = 20
    page.scroll = ft.ScrollMode.AUTO

    if not hasattr(page, 'session_data'):
        page.session_data = SessionData()

    await connection(page)


ft.app(target=main, view=ft.AppView.WEB_BROWSER)
