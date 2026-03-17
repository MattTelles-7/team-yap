#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use reqwest::Client;
use serde::{Deserialize, Serialize};
use std::fs;
use std::path::PathBuf;
use tauri::{AppHandle, Manager};

const SETTINGS_FILE_NAME: &str = "settings.json";
const DEFAULT_SERVER_URL: &str = "http://127.0.0.1:8080";
const DEFAULT_THEME: &str = "dark";

fn default_server_url() -> String {
    DEFAULT_SERVER_URL.into()
}

fn default_theme() -> String {
    DEFAULT_THEME.into()
}

#[derive(Clone, Debug, Deserialize, Serialize)]
struct AppSettings {
    #[serde(default = "default_server_url")]
    server_url: String,
    #[serde(default)]
    auth_token: Option<String>,
    #[serde(default = "default_theme")]
    theme: String,
}

#[derive(Clone, Debug, Deserialize)]
struct LoginPayload {
    token: String,
    user: ApiUser,
}

#[derive(Clone, Debug, Deserialize)]
struct ApiUser {
    id: i64,
    username: String,
    display_name: String,
    is_admin: bool,
}

#[derive(Clone, Debug, Deserialize)]
struct ApiMessage {
    id: i64,
    body: String,
    created_at: String,
    author_username: String,
    author_display_name: String,
}

#[derive(Clone, Debug, Serialize)]
#[serde(rename_all = "camelCase")]
struct SettingsPayload {
    server_url: String,
    has_saved_session: bool,
    theme: String,
}

#[derive(Clone, Debug, Serialize)]
#[serde(rename_all = "camelCase")]
struct UserPayload {
    id: i64,
    username: String,
    display_name: String,
    is_admin: bool,
}

#[derive(Clone, Debug, Serialize)]
#[serde(rename_all = "camelCase")]
struct SessionPayload {
    authenticated: bool,
    server_url: String,
    user: Option<UserPayload>,
}

#[derive(Clone, Debug, Serialize)]
#[serde(rename_all = "camelCase")]
struct MessagePayload {
    id: i64,
    body: String,
    created_at: String,
    author_username: String,
    author_display_name: String,
}

#[derive(Debug, Serialize)]
struct LoginRequest<'a> {
    username: &'a str,
    password: &'a str,
}

#[derive(Debug, Serialize)]
struct CreateMessageRequest<'a> {
    body: &'a str,
}

impl From<ApiUser> for UserPayload {
    fn from(value: ApiUser) -> Self {
        Self {
            id: value.id,
            username: value.username,
            display_name: value.display_name,
            is_admin: value.is_admin,
        }
    }
}

impl From<ApiMessage> for MessagePayload {
    fn from(value: ApiMessage) -> Self {
        Self {
            id: value.id,
            body: value.body,
            created_at: value.created_at,
            author_username: value.author_username,
            author_display_name: value.author_display_name,
        }
    }
}

fn normalize_server_url(raw: &str) -> Result<String, String> {
    let trimmed = raw.trim().trim_end_matches('/').to_string();
    if trimmed.is_empty() {
        return Err("Server URL is required.".into());
    }
    if !trimmed.starts_with("http://") && !trimmed.starts_with("https://") {
        return Err("Server URL must start with http:// or https://.".into());
    }
    Ok(trimmed)
}

fn normalize_theme(raw: &str) -> Result<String, String> {
    match raw.trim().to_ascii_lowercase().as_str() {
        "dark" => Ok("dark".into()),
        "light" => Ok("light".into()),
        _ => Err("Theme must be either dark or light.".into()),
    }
}

fn config_dir(app: &AppHandle) -> Result<PathBuf, String> {
    let dir = app
        .path()
        .app_config_dir()
        .map_err(|error| format!("Could not resolve the app config directory: {error}"))?;
    fs::create_dir_all(&dir)
        .map_err(|error| format!("Could not create the app config directory: {error}"))?;
    Ok(dir)
}

fn settings_path(app: &AppHandle) -> Result<PathBuf, String> {
    Ok(config_dir(app)?.join(SETTINGS_FILE_NAME))
}

fn read_settings(app: &AppHandle) -> Result<AppSettings, String> {
    let path = settings_path(app)?;
    if !path.exists() {
        return Ok(AppSettings::default());
    }

    let raw = fs::read_to_string(&path)
        .map_err(|error| format!("Could not read settings from {}: {error}", path.display()))?;
    let mut settings: AppSettings =
        serde_json::from_str(&raw).map_err(|error| format!("Invalid settings file: {error}"))?;
    if settings.server_url.trim().is_empty() {
        settings.server_url = default_server_url();
    }
    settings.theme = normalize_theme(&settings.theme).unwrap_or_else(|_| default_theme());
    Ok(settings)
}

fn write_settings(app: &AppHandle, settings: &AppSettings) -> Result<(), String> {
    let path = settings_path(app)?;
    let body = serde_json::to_string_pretty(settings)
        .map_err(|error| format!("Could not serialize settings: {error}"))?;
    fs::write(&path, body)
        .map_err(|error| format!("Could not write settings to {}: {error}", path.display()))
}

fn public_settings(settings: &AppSettings) -> SettingsPayload {
    SettingsPayload {
        server_url: settings.server_url.clone(),
        has_saved_session: settings.auth_token.is_some(),
        theme: settings.theme.clone(),
    }
}

fn session_payload(settings: &AppSettings, user: Option<UserPayload>) -> SessionPayload {
    SessionPayload {
        authenticated: user.is_some(),
        server_url: settings.server_url.clone(),
        user,
    }
}

fn http_client() -> Result<Client, String> {
    Client::builder()
        .user_agent("Team Yap Desktop/0.1.0")
        .build()
        .map_err(|error| format!("Could not create the HTTP client: {error}"))
}

async fn get_authenticated_settings(app: &AppHandle) -> Result<AppSettings, String> {
    let settings = read_settings(app)?;
    if settings.server_url.is_empty() {
        return Err("Save a server URL before trying to talk to the server.".into());
    }
    if settings.auth_token.is_none() {
        return Err("No saved session was found. Sign in first.".into());
    }
    Ok(settings)
}

#[tauri::command]
fn load_settings(app: AppHandle) -> Result<SettingsPayload, String> {
    read_settings(&app).map(|settings| public_settings(&settings))
}

#[tauri::command]
fn save_server_url(app: AppHandle, server_url: String) -> Result<SettingsPayload, String> {
    let mut settings = read_settings(&app)?;
    settings.server_url = normalize_server_url(&server_url)?;
    settings.auth_token = None;
    write_settings(&app, &settings)?;
    Ok(public_settings(&settings))
}

#[tauri::command]
fn save_theme(app: AppHandle, theme: String) -> Result<SettingsPayload, String> {
    let mut settings = read_settings(&app)?;
    settings.theme = normalize_theme(&theme)?;
    write_settings(&app, &settings)?;
    Ok(public_settings(&settings))
}

#[tauri::command]
async fn login(
    app: AppHandle,
    server_url: String,
    username: String,
    password: String,
) -> Result<SessionPayload, String> {
    let normalized_server_url = normalize_server_url(&server_url)?;
    let client = http_client()?;
    let response = client
        .post(format!("{normalized_server_url}/api/auth/login"))
        .json(&LoginRequest {
            username: username.trim(),
            password: password.as_str(),
        })
        .send()
        .await
        .map_err(|error| format!("Could not reach the server: {error}"))?;

    if !response.status().is_success() {
        let detail = response
            .text()
            .await
            .unwrap_or_else(|_| "Login failed.".into());
        return Err(format!("Login failed: {detail}"));
    }

    let payload: LoginPayload = response
        .json()
        .await
        .map_err(|error| format!("Could not parse the login response: {error}"))?;

    let user = UserPayload::from(payload.user);
    let mut settings = read_settings(&app)?;
    settings.server_url = normalized_server_url;
    settings.auth_token = Some(payload.token);
    write_settings(&app, &settings)?;
    Ok(session_payload(&settings, Some(user)))
}

#[tauri::command]
async fn resume_session(app: AppHandle) -> Result<SessionPayload, String> {
    let mut settings = read_settings(&app)?;
    let Some(token) = settings.auth_token.clone() else {
        return Ok(session_payload(&settings, None));
    };

    let client = http_client()?;
    let response = client
        .get(format!("{}/api/auth/me", settings.server_url))
        .bearer_auth(token)
        .send()
        .await
        .map_err(|error| format!("Could not reach the server: {error}"))?;

    if response.status().is_success() {
        let user: ApiUser = response
            .json()
            .await
            .map_err(|error| format!("Could not parse the session response: {error}"))?;
        return Ok(session_payload(&settings, Some(UserPayload::from(user))));
    }

    settings.auth_token = None;
    write_settings(&app, &settings)?;
    Ok(session_payload(&settings, None))
}

#[tauri::command]
async fn list_messages(app: AppHandle) -> Result<Vec<MessagePayload>, String> {
    let settings = get_authenticated_settings(&app).await?;
    let client = http_client()?;
    let response = client
        .get(format!("{}/api/messages", settings.server_url))
        .bearer_auth(settings.auth_token.unwrap_or_default())
        .send()
        .await
        .map_err(|error| format!("Could not load messages: {error}"))?;

    if !response.status().is_success() {
        let detail = response
            .text()
            .await
            .unwrap_or_else(|_| "Message request failed.".into());
        return Err(format!("Could not load messages: {detail}"));
    }

    let messages: Vec<ApiMessage> = response
        .json()
        .await
        .map_err(|error| format!("Could not parse the messages response: {error}"))?;

    Ok(messages.into_iter().map(MessagePayload::from).collect())
}

#[tauri::command]
async fn post_message(app: AppHandle, body: String) -> Result<MessagePayload, String> {
    let trimmed = body.trim().to_string();
    if trimmed.is_empty() {
        return Err("Write a message before posting it.".into());
    }

    let settings = get_authenticated_settings(&app).await?;
    let client = http_client()?;
    let response = client
        .post(format!("{}/api/messages", settings.server_url))
        .bearer_auth(settings.auth_token.unwrap_or_default())
        .json(&CreateMessageRequest { body: &trimmed })
        .send()
        .await
        .map_err(|error| format!("Could not post the message: {error}"))?;

    if !response.status().is_success() {
        let detail = response
            .text()
            .await
            .unwrap_or_else(|_| "Posting the message failed.".into());
        return Err(format!("Could not post the message: {detail}"));
    }

    let message: ApiMessage = response
        .json()
        .await
        .map_err(|error| format!("Could not parse the message response: {error}"))?;
    Ok(MessagePayload::from(message))
}

#[tauri::command]
async fn logout(app: AppHandle) -> Result<(), String> {
    let mut settings = read_settings(&app)?;

    if let Some(token) = settings.auth_token.clone() {
        let client = http_client()?;
        let _ = client
            .post(format!("{}/api/auth/logout", settings.server_url))
            .bearer_auth(token)
            .send()
            .await;
    }

    settings.auth_token = None;
    write_settings(&app, &settings)
}

fn main() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![
            load_settings,
            save_server_url,
            save_theme,
            login,
            resume_session,
            list_messages,
            post_message,
            logout
        ])
        .run(tauri::generate_context!())
        .expect("error while running Team Yap");
}

impl Default for AppSettings {
    fn default() -> Self {
        Self {
            server_url: default_server_url(),
            auth_token: None,
            theme: default_theme(),
        }
    }
}
