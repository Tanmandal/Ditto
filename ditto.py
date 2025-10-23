import flet as ft
import json

API_BASE_URL = "https://short-url.leapcell.app"


class SessionData:
    def __init__(self):
        self.access_token = None
        self.current_alias = None


# Ditto Pokemon image
ditto_image = ft.Image(
    src="https://ik.imagekit.io/2zdmk9mex/uploads/avatar.png?updatedAt=1761076843950",
    width=80,
    height=80,
    fit=ft.ImageFit.CONTAIN,
)


async def make_request(page: ft.Page, url, method="GET", data=None, timeout=10):
    """
    HTTP request that works in both desktop and web builds
    """
    try:
        import sys
        if 'pyodide' in sys.modules:
            # Running in browser - use JavaScript fetch
            return await make_request_js(page, url, method, data)
        else:
            # Running in desktop - use urllib
            return make_request_urllib(url, method, data, timeout)
    except Exception as e:
        return {
            'ok': False,
            'status': 0,
            'body': {'detail': f'Error: {str(e)}'}
        }


async def make_request_js(page: ft.Page, url, method="GET", data=None):
    """Use JavaScript fetch for browser environment"""
    import js
    from pyodide.ffi import to_js, JsException

    options = {
        'method': method,
        'headers': {'Content-Type': 'application/json'}
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


def make_request_urllib(url, method="GET", data=None, timeout=10):
    """Original urllib implementation for desktop"""
    import urllib.request
    import urllib.error

    try:
        if data:
            data = json.dumps(data).encode('utf-8')

        req = urllib.request.Request(
            url,
            data=data,
            headers={'Content-Type': 'application/json'} if data else {},
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

                status_text.value = "Login successful!"
                status_text.color = "#5ab896"
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

    def on_link_click(e):
        page.controls.clear()
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
    try:
        response = await make_request(page, f"{API_BASE_URL}/health", timeout=10)
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
