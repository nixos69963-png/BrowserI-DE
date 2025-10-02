from flask import Flask, render_template_string, request, jsonify
import os
import subprocess
import pwd
import json

app = Flask(__name__)

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>VSCode Web</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.2/codemirror.min.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.2/theme/monokai.min.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.2/addon/fold/foldgutter.min.css">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/xterm@4.19.0/css/xterm.css" />
    <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.2/codemirror.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.2/mode/python/python.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.2/mode/javascript/javascript.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.2/mode/css/css.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.2/mode/htmlmixed/htmlmixed.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.2/mode/xml/xml.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.2/mode/shell/shell.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.2/mode/markdown/markdown.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.2/addon/fold/foldcode.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.2/addon/fold/foldgutter.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.2/addon/fold/brace-fold.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.2/addon/fold/indent-fold.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/xterm@4.19.0/lib/xterm.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            height: 100vh;
            overflow: hidden;
            background: #1e1e1e;
            color: #cccccc;
        }

        .activity-bar {
            width: 48px;
            background: #333333;
            display: flex;
            flex-direction: column;
            padding: 8px 0;
            border-right: 1px solid #2d2d2d;
        }

        .activity-icon {
            width: 48px;
            height: 48px;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            position: relative;
            color: #858585;
            transition: color 0.15s ease;
        }

        .activity-icon:hover { color: #ffffff; }
        .activity-icon.active {
            color: #ffffff;
        }

        .activity-icon.active::before {
            content: '';
            position: absolute;
            left: 0;
            top: 0;
            bottom: 0;
            width: 2px;
            background: #007acc;
        }

        .activity-icon svg {
            width: 24px;
            height: 24px;
        }

        .activity-spacer {
            flex: 1;
        }

        .sidebar {
            width: 300px;
            background: #252526;
            display: flex;
            flex-direction: column;
            border-right: 1px solid #2d2d2d;
            transition: width 0.2s ease;
        }

        .sidebar.collapsed {
            width: 0;
            overflow: hidden;
        }

        .sidebar-header {
            padding: 12px 20px;
            font-size: 11px;
            text-transform: uppercase;
            color: #cccccc;
            font-weight: 600;
            letter-spacing: 0.5px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: #252526;
            border-bottom: 1px solid #2d2d2d;
        }

        .sidebar-actions {
            display: flex;
            gap: 8px;
        }

        .sidebar-action {
            cursor: pointer;
            color: #cccccc;
            padding: 2px;
            border-radius: 3px;
            transition: background 0.15s ease;
        }

        .sidebar-action:hover {
            background: rgba(255, 255, 255, 0.1);
        }

        .sidebar-content {
            flex: 1;
            overflow-y: auto;
            padding: 4px 0;
        }

        .folder-section {
            margin-bottom: 8px;
        }

        .folder-header {
            padding: 6px 12px;
            font-size: 11px;
            text-transform: uppercase;
            color: #cccccc;
            font-weight: 600;
            letter-spacing: 0.5px;
            display: flex;
            align-items: center;
            gap: 6px;
            cursor: pointer;
            user-select: none;
        }

        .folder-header:hover {
            background: rgba(255, 255, 255, 0.05);
        }

        .folder-chevron {
            font-size: 10px;
            transition: transform 0.15s ease;
            display: inline-block;
        }

        .folder-section.collapsed .folder-chevron {
            transform: rotate(-90deg);
        }

        .folder-section.collapsed .folder-items {
            display: none;
        }

        .tree-item {
            padding: 4px 8px 4px 20px;
            cursor: pointer;
            display: flex;
            align-items: center;
            font-size: 13px;
            color: #cccccc;
            transition: background 0.1s ease;
            user-select: none;
            position: relative;
        }

        .tree-item:hover {
            background: #2a2d2e;
        }

        .tree-item.selected {
            background: #37373d;
        }

        .tree-item.modified::after {
            content: '●';
            position: absolute;
            right: 12px;
            color: #ffffff;
            font-size: 16px;
        }

        .tree-item-icon {
            margin-right: 6px;
            font-size: 14px;
            width: 16px;
            text-align: center;
        }

        .tree-item.folder {
            font-weight: 500;
        }

        .tree-item.indent-1 { padding-left: 28px; }
        .tree-item.indent-2 { padding-left: 44px; }
        .tree-item.indent-3 { padding-left: 60px; }
        .tree-item.indent-4 { padding-left: 76px; }

        .main-container {
            display: flex;
            height: 100vh;
        }

        .editor-container {
            flex: 1;
            display: flex;
            flex-direction: column;
            background: #1e1e1e;
            min-width: 0;
        }

        .title-bar {
            height: 35px;
            background: #3c3c3c;
            display: flex;
            align-items: center;
            padding: 0 16px;
            justify-content: center;
            color: #cccccc;
            font-size: 13px;
            border-bottom: 1px solid #2d2d2d;
            user-select: none;
        }

        .tabs-container {
            height: 35px;
            background: #2d2d2d;
            display: flex;
            align-items: center;
            border-bottom: 1px solid #252526;
            overflow-x: auto;
            overflow-y: hidden;
        }

        .tabs-container::-webkit-scrollbar {
            height: 0;
        }

        .tab {
            height: 35px;
            padding: 0 12px;
            display: flex;
            align-items: center;
            gap: 8px;
            background: #2d2d2d;
            border-right: 1px solid #252526;
            cursor: pointer;
            font-size: 13px;
            color: #969696;
            transition: background 0.1s ease, color 0.1s ease;
            white-space: nowrap;
            min-width: 120px;
            flex-shrink: 0;
            position: relative;
        }

        .tab:hover {
            background: #1e1e1e;
            color: #ffffff;
        }

        .tab.active {
            background: #1e1e1e;
            color: #ffffff;
        }

        .tab.active::after {
            content: '';
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            height: 1px;
            background: #007acc;
        }

        .tab.modified .tab-title::after {
            content: '●';
            margin-left: 4px;
            color: #ffffff;
        }

        .tab-close {
            margin-left: auto;
            font-size: 18px;
            opacity: 0;
            transition: opacity 0.15s ease;
            width: 20px;
            height: 20px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 3px;
        }

        .tab:hover .tab-close,
        .tab.active .tab-close {
            opacity: 0.6;
        }

        .tab-close:hover {
            opacity: 1 !important;
            background: rgba(255, 255, 255, 0.1);
        }

        .editor-area {
            flex: 1;
            display: flex;
            flex-direction: column;
            overflow: hidden;
            position: relative;
        }

        .CodeMirror {
            height: 100% !important;
            font-family: 'Consolas', 'Monaco', 'Menlo', 'Courier New', monospace;
            font-size: 14px;
            line-height: 1.6;
        }

        .CodeMirror-gutters {
            background: #1e1e1e;
            border-right: 1px solid #2d2d2d;
        }

        .CodeMirror-linenumber {
            color: #858585;
            padding: 0 8px;
        }

        .editor-placeholder {
            flex: 1;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-direction: column;
            color: #6a737d;
            font-size: 14px;
        }

        .editor-placeholder svg {
            width: 64px;
            height: 64px;
            margin-bottom: 16px;
            opacity: 0.3;
        }

        .welcome-actions {
            margin-top: 24px;
            display: flex;
            flex-direction: column;
            gap: 8px;
        }

        .welcome-action {
            padding: 8px 16px;
            background: #0e639c;
            border: 1px solid #007acc;
            color: #ffffff;
            border-radius: 3px;
            cursor: pointer;
            font-size: 13px;
            transition: background 0.15s ease;
        }

        .welcome-action:hover {
            background: #1177bb;
        }

        .terminal-container {
            height: 250px;
            background: #1e1e1e;
            border-top: 1px solid #2d2d2d;
            display: flex;
            flex-direction: column;
            position: relative;
        }

        .terminal-container.hidden {
            display: none;
        }

        .terminal-resize-handle {
            position: absolute;
            top: -3px;
            left: 0;
            right: 0;
            height: 6px;
            cursor: ns-resize;
            z-index: 10;
        }

        .terminal-resize-handle:hover {
            background: rgba(0, 122, 204, 0.5);
        }

        .terminal-header {
            height: 35px;
            background: #252526;
            display: flex;
            align-items: center;
            padding: 0 12px;
            justify-content: space-between;
            border-bottom: 1px solid #2d2d2d;
        }

        .terminal-tabs {
            display: flex;
            gap: 2px;
        }

        .terminal-tab {
            padding: 6px 12px;
            font-size: 12px;
            background: #1e1e1e;
            border-radius: 3px 3px 0 0;
            cursor: pointer;
            color: #cccccc;
        }

        .terminal-actions {
            display: flex;
            gap: 12px;
            align-items: center;
        }

        .terminal-action {
            cursor: pointer;
            padding: 4px;
            color: #cccccc;
            font-size: 16px;
            transition: color 0.15s ease;
        }

        .terminal-action:hover {
            color: #ffffff;
        }

        .terminal-body {
            flex: 1;
            padding: 8px;
            overflow: hidden;
        }

        .status-bar {
            height: 22px;
            background: #007acc;
            display: flex;
            align-items: center;
            padding: 0 12px;
            font-size: 12px;
            color: #ffffff;
            justify-content: space-between;
            user-select: none;
        }

        .status-left, .status-right {
            display: flex;
            gap: 16px;
            align-items: center;
        }

        .status-item {
            display: flex;
            align-items: center;
            gap: 4px;
            cursor: pointer;
            padding: 2px 6px;
            border-radius: 3px;
            transition: background 0.15s ease;
        }

        .status-item:hover {
            background: rgba(255, 255, 255, 0.1);
        }

        ::-webkit-scrollbar {
            width: 10px;
            height: 10px;
        }

        ::-webkit-scrollbar-track {
            background: #1e1e1e;
        }

        ::-webkit-scrollbar-thumb {
            background: #424242;
            border-radius: 5px;
        }

        ::-webkit-scrollbar-thumb:hover {
            background: #4e4e4e;
        }

        .context-menu {
            position: fixed;
            background: #3c3c3c;
            border: 1px solid #454545;
            box-shadow: 0 4px 16px rgba(0,0,0,0.6);
            border-radius: 5px;
            padding: 4px 0;
            min-width: 200px;
            z-index: 1000;
            display: none;
        }

        .context-menu-item {
            padding: 6px 32px 6px 20px;
            font-size: 13px;
            cursor: pointer;
            color: #cccccc;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .context-menu-item:hover {
            background: #094771;
            color: #ffffff;
        }

        .context-menu-separator {
            height: 1px;
            background: #454545;
            margin: 4px 0;
        }

        .context-menu-shortcut {
            font-size: 11px;
            color: #858585;
            margin-left: 24px;
        }

        .breadcrumb {
            height: 28px;
            background: #252526;
            display: flex;
            align-items: center;
            padding: 0 12px;
            font-size: 12px;
            color: #969696;
            border-bottom: 1px solid #2d2d2d;
        }

        .breadcrumb-item {
            display: flex;
            align-items: center;
            gap: 4px;
            cursor: pointer;
            padding: 2px 6px;
            border-radius: 3px;
            transition: background 0.15s ease;
        }

        .breadcrumb-item:hover {
            background: rgba(255, 255, 255, 0.05);
            color: #cccccc;
        }

        .breadcrumb-separator {
            margin: 0 4px;
            color: #6a737d;
        }

        .notification {
            position: fixed;
            bottom: 30px;
            right: 20px;
            background: #252526;
            border: 1px solid #454545;
            border-radius: 5px;
            padding: 12px 16px;
            min-width: 300px;
            max-width: 400px;
            box-shadow: 0 4px 16px rgba(0,0,0,0.6);
            z-index: 1000;
            display: flex;
            gap: 12px;
            align-items: flex-start;
            animation: slideIn 0.3s ease;
        }

        @keyframes slideIn {
            from {
                transform: translateX(400px);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }

        .notification-icon {
            font-size: 20px;
        }

        .notification-content {
            flex: 1;
        }

        .notification-title {
            font-weight: 600;
            margin-bottom: 4px;
            color: #cccccc;
        }

        .notification-message {
            font-size: 12px;
            color: #969696;
        }

        .notification-close {
            cursor: pointer;
            color: #858585;
            font-size: 18px;
            padding: 0 4px;
        }

        .notification-close:hover {
            color: #cccccc;
        }

        .command-palette {
            position: fixed;
            top: 80px;
            left: 50%;
            transform: translateX(-50%);
            background: #252526;
            border: 1px solid #454545;
            border-radius: 5px;
            width: 600px;
            max-height: 400px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.8);
            z-index: 1000;
            display: none;
            flex-direction: column;
        }

        .command-palette.visible {
            display: flex;
        }

        .command-input {
            padding: 12px 16px;
            background: #3c3c3c;
            border: none;
            border-bottom: 1px solid #454545;
            color: #cccccc;
            font-size: 14px;
            outline: none;
        }

        .command-list {
            flex: 1;
            overflow-y: auto;
            padding: 4px 0;
        }

        .command-item {
            padding: 8px 16px;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 12px;
            color: #cccccc;
            font-size: 13px;
        }

        .command-item:hover,
        .command-item.selected {
            background: #094771;
        }

        .command-item-icon {
            font-size: 16px;
        }

        .command-item-text {
            flex: 1;
        }

        .command-item-shortcut {
            font-size: 11px;
            color: #858585;
        }

        .loading {
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            display: none;
        }

        .loading.visible {
            display: block;
        }

        .spinner {
            width: 40px;
            height: 40px;
            border: 4px solid rgba(255, 255, 255, 0.1);
            border-top-color: #007acc;
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="main-container">
        <div class="activity-bar">
            <div class="activity-icon active" onclick="toggleSidebar('explorer')" title="Explorer (Ctrl+Shift+E)">
                <svg viewBox="0 0 16 16" fill="currentColor">
                    <path d="M14.5 2H7.71l-.85-.85L6.51 1h-5l-.5.5v11l.5.5h13l.5-.5v-10zm-.51 8.49V13h-12V7h4.49l.35-.15.86-.86H14v4.5z"/>
                </svg>
            </div>
            <div class="activity-icon" onclick="toggleSidebar('search')" title="Search (Ctrl+Shift+F)">
                <svg viewBox="0 0 16 16" fill="currentColor">
                    <path d="M11.5 7a4.5 4.5 0 1 1-9 0 4.5 4.5 0 0 1 9 0zm-.82 4.74a6 6 0 1 1 1.06-1.06l3.04 3.04a.75.75 0 1 1-1.06 1.06l-3.04-3.04z"/>
                </svg>
            </div>
            <div class="activity-icon" onclick="toggleSidebar('git')" title="Source Control (Ctrl+Shift+G)">
                <svg viewBox="0 0 16 16" fill="currentColor">
                    <path d="M11.5 2.5a2 2 0 1 0 0 4 2 2 0 0 0 0-4zm-1 2a1 1 0 1 1 2 0 1 1 0 0 1-2 0zM4.5 9.5a2 2 0 1 0 0 4 2 2 0 0 0 0-4zm-1 2a1 1 0 1 1 2 0 1 1 0 0 1-2 0z"/>
                </svg>
            </div>
            <div class="activity-spacer"></div>
            <div class="activity-icon" onclick="showSettings()" title="Settings (Ctrl+,)">
                <svg viewBox="0 0 16 16" fill="currentColor">
                    <path d="M8 5.5a2.5 2.5 0 1 0 0 5 2.5 2.5 0 0 0 0-5zM6 8a2 2 0 1 1 4 0 2 2 0 0 1-4 0z"/>
                </svg>
            </div>
        </div>

        <div class="sidebar" id="sidebar">
            <div class="sidebar-header">
                <span id="sidebar-title">EXPLORER</span>
                <div class="sidebar-actions">
                    <span class="sidebar-action" onclick="createNewFile()" title="New File">📄</span>
                    <span class="sidebar-action" onclick="createNewFolder()" title="New Folder">📁</span>
                    <span class="sidebar-action" onclick="refreshExplorer()" title="Refresh Explorer">↻</span>
                </div>
            </div>
            <div class="sidebar-content" id="sidebar-content">
                <div class="folder-section">
                    <div class="folder-header" onclick="toggleFolderSection(this)">
                        <span class="folder-chevron">▼</span>
                        <span>WORKSPACE</span>
                    </div>
                    <div class="folder-items" id="file-tree"></div>
                </div>
            </div>
        </div>

        <div class="editor-container">
            <div class="title-bar">
                <span>Visual Studio Code - Web Edition</span>
            </div>

            <div class="breadcrumb" id="breadcrumb">
                <span style="color: #858585;">No file selected</span>
            </div>

            <div class="tabs-container" id="tabs-container"></div>

            <div class="editor-area">
                <div class="editor-placeholder" id="editor-placeholder">
                    <svg viewBox="0 0 24 24" fill="currentColor">
                        <path d="M14 2H6c-1.1 0-2 .9-2 2v16c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V8l-6-6zM6 20V4h7v5h5v11H6z"/>
                    </svg>
                    <div>Start typing or open a file</div>
                    <div class="welcome-actions">
                        <button class="welcome-action" onclick="createNewFile()">New File</button>
                        <button class="welcome-action" onclick="toggleCommandPalette()">Open Command Palette (Ctrl+Shift+P)</button>
                    </div>
                </div>
                <textarea id="editor" style="display:none;"></textarea>
            </div>

            <div class="terminal-container hidden" id="terminal-container">
                <div class="terminal-resize-handle" id="terminal-resize"></div>
                <div class="terminal-header">
                    <div class="terminal-tabs">
                        <div class="terminal-tab">bash</div>
                    </div>
                    <div class="terminal-actions">
                        <span class="terminal-action" onclick="splitTerminal()" title="Split Terminal">⊞</span>
                        <span class="terminal-action" onclick="clearTerminal()" title="Clear Terminal">🗑</span>
                        <span class="terminal-action" onclick="toggleTerminal()" title="Close Terminal">✕</span>
                    </div>
                </div>
                <div class="terminal-body" id="terminal-body"></div>
            </div>

            <div class="status-bar">
                <div class="status-left">
                    <div class="status-item" title="Source Control">
                        <span>⎇</span>
                        <span>main</span>
                    </div>
                    <div class="status-item" id="status-errors" title="Problems">
                        <span>✕</span>
                        <span>0</span>
                    </div>
                    <div class="status-item" id="status-warnings">
                        <span>⚠</span>
                        <span>0</span>
                    </div>
                </div>
                <div class="status-right">
                    <div class="status-item" id="status-position">Ln 1, Col 1</div>
                    <div class="status-item" id="status-language">Plain Text</div>
                    <div class="status-item" id="status-encoding">UTF-8</div>
                    <div class="status-item" id="status-eol">LF</div>
                    <div class="status-item" onclick="toggleTerminal()" title="Toggle Terminal">⌨ Terminal</div>
                </div>
            </div>
        </div>
    </div>

    <div class="command-palette" id="command-palette">
        <input type="text" class="command-input" id="command-input" placeholder="Type a command or search...">
        <div class="command-list" id="command-list"></div>
    </div>

    <div class="context-menu" id="context-menu">
        <div class="context-menu-item" onclick="contextAction('cut')">
            Cut <span class="context-menu-shortcut">Ctrl+X</span>
        </div>
        <div class="context-menu-item" onclick="contextAction('copy')">
            Copy <span class="context-menu-shortcut">Ctrl+C</span>
        </div>
        <div class="context-menu-item" onclick="contextAction('paste')">
            Paste <span class="context-menu-shortcut">Ctrl+V</span>
        </div>
        <div class="context-menu-separator"></div>
        <div class="context-menu-item" onclick="contextAction('rename')">
            Rename <span class="context-menu-shortcut">F2</span>
        </div>
        <div class="context-menu-item" onclick="contextAction('delete')">
            Delete <span class="context-menu-shortcut">Del</span>
        </div>
    </div>

    <div class="loading" id="loading">
        <div class="spinner"></div>
    </div>

    <script>
        let editor = CodeMirror.fromTextArea(document.getElementById('editor'), {
            lineNumbers: true,
            theme: 'monokai',
            mode: 'python',
            lineWrapping: false,
            indentUnit: 4,
            tabSize: 4,
            matchBrackets: true,
            autoCloseBrackets: true,
            foldGutter: true,
            gutters: ["CodeMirror-linenumbers", "CodeMirror-foldgutter"],
            extraKeys: {
                "Ctrl-S": () => saveCurrentFile(),
                "Cmd-S": () => saveCurrentFile(),
                "Ctrl-`": () => toggleTerminal(),
                "Ctrl-W": () => activeTab && closeTab(activeTab.path),
                "Ctrl-Shift-P": () => toggleCommandPalette(),
                "Ctrl-P": () => toggleQuickOpen(),
                "Ctrl-B": () => toggleSidebar(),
                "F2": () => renameFile()
            }
        });

        let openTabs = [];
        let activeTab = null;
        let terminal = null;
        let commandBuffer = '';
        let currentDir = '';
        let username = '';
        let hostname = '';
        let currentSidebar = 'explorer';
        let expandedFolders = new Set();

        initializeEditor();
        loadDirectory('/');

        function initializeEditor() {
            editor.on('cursorActivity', () => {
                const cursor = editor.getCursor();
                document.getElementById('status-position').textContent = `Ln ${cursor.line + 1}, Col ${cursor.ch + 1}`;
            });

            editor.on('change', () => {
                if (activeTab) {
                    activeTab.modified = true;
                    activeTab.content = editor.getValue();
                    renderTabs();
                    updateFileTree();
                }
            });

            document.addEventListener('contextmenu', (e) => {
                e.preventDefault();
                showContextMenu(e.clientX, e.clientY);
            });

            document.addEventListener('click', () => {
                hideContextMenu();
                hideCommandPalette();
            });

            document.addEventListener('keydown', (e) => {
                if (e.ctrlKey || e.metaKey) {
                    if (e.shiftKey && e.key === 'P') {
                        e.preventDefault();
                        toggleCommandPalette();
                    } else if (e.key === 'p') {
                        e.preventDefault();
                        toggleQuickOpen();
                    } else if (e.key === 's') {
                        e.preventDefault();
                        saveCurrentFile();
                    } else if (e.key === '`') {
                        e.preventDefault();
                        toggleTerminal();
                    } else if (e.key === 'w') {
                        e.preventDefault();
                        if (activeTab) closeTab(activeTab.path);
                    } else if (e.key === 'b') {
                        e.preventDefault();
                        toggleSidebar();
                    }
                }
                if (e.key === 'F2') {
                    e.preventDefault();
                    renameFile();
                }
            });

            initTerminalResize();
        }

        function loadDirectory(path = '/', parentElement = null, indent = 0) {
            fetch('/list?path=' + encodeURIComponent(path))
                .then(r => r.json())
                .then(data => {
                    if (data.error) {
                        showNotification('Error', data.error, 'error');
                        return;
                    }
                    
                    const container = parentElement || document.getElementById('file-tree');
                    
                    if (!parentElement) {
                        container.innerHTML = '';
                    }
                    
                    const items = [
                        ...data.folders.map(f => ({...f, type: 'folder'})),
                        ...data.files.map(f => ({...f, type: 'file'}))
                    ];
                    
                    items.forEach(item => {
                        const itemEl = document.createElement('div');
                        itemEl.className = `tree-item ${item.type} indent-${indent}`;
                        itemEl.dataset.path = item.path;
                        
                        const icon = item.type === 'folder' ? '📁' : getFileIcon(item.name);
                        const chevron = item.type === 'folder' ? '<span style="margin-right: 4px; font-size: 10px;">▸</span>' : '';
                        
                        itemEl.innerHTML = `${chevron}<span class="tree-item-icon">${icon}</span>${item.name}`;
                        
                        if (item.type === 'folder') {
                            itemEl.onclick = (e) => {
                                e.stopPropagation();
                                toggleFolder(itemEl, item.path, indent);
                            };
                        } else {
                            itemEl.onclick = (e) => {
                                e.stopPropagation();
                                openFile(item.path);
                                selectTreeItem(itemEl);
                            };
                        }
                        
                        container.appendChild(itemEl);
                    });
                });
        }

        function toggleFolder(element, path, indent) {
            const isExpanded = expandedFolders.has(path);
            
            if (isExpanded) {
                expandedFolders.delete(path);
                let next = element.nextElementSibling;
                while (next && next.classList.contains(`indent-${indent + 1}`)) {
                    const toRemove = next;
                    next = next.nextElementSibling;
                    toRemove.remove();
                }
                element.querySelector('span').textContent = '▸';
            } else {
                expandedFolders.add(path);
                element.querySelector('span').textContent = '▾';
                
                fetch('/list?path=' + encodeURIComponent(path))
                    .then(r => r.json())
                    .then(data => {
                        if (data.error) return;
                        
                        const items = [
                            ...data.folders.map(f => ({...f, type: 'folder'})),
                            ...data.files.map(f => ({...f, type: 'file'}))
                        ];
                        
                        items.reverse().forEach(item => {
                            const itemEl = document.createElement('div');
                            itemEl.className = `tree-item ${item.type} indent-${indent + 1}`;
                            itemEl.dataset.path = item.path;
                            
                            const icon = item.type === 'folder' ? '📁' : getFileIcon(item.name);
                            const chevron = item.type === 'folder' ? '<span style="margin-right: 4px; font-size: 10px;">▸</span>' : '';
                            
                            itemEl.innerHTML = `${chevron}<span class="tree-item-icon">${icon}</span>${item.name}`;
                            
                            if (item.type === 'folder') {
                                itemEl.onclick = (e) => {
                                    e.stopPropagation();
                                    toggleFolder(itemEl, item.path, indent + 1);
                                };
                            } else {
                                itemEl.onclick = (e) => {
                                    e.stopPropagation();
                                    openFile(item.path);
                                    selectTreeItem(itemEl);
                                };
                            }
                            
                            element.insertAdjacentElement('afterend', itemEl);
                        });
                    });
            }
        }

        function selectTreeItem(element) {
            document.querySelectorAll('.tree-item').forEach(el => el.classList.remove('selected'));
            element.classList.add('selected');
        }

        function updateFileTree() {
            openTabs.forEach(tab => {
                const item = document.querySelector(`.tree-item[data-path="${tab.path}"]`);
                if (item) {
                    if (tab.modified) {
                        item.classList.add('modified');
                    } else {
                        item.classList.remove('modified');
                    }
                }
            });
        }

        function getFileIcon(filename) {
            const ext = filename.split('.').pop().toLowerCase();
            const icons = {
                'py': '🐍', 'js': '📜', 'jsx': '⚛️', 'ts': '📘', 'tsx': '⚛️',
                'html': '🌐', 'css': '🎨', 'scss': '🎨', 'json': '📋',
                'md': '📝', 'txt': '📄', 'sh': '⚙️', 'bash': '⚙️',
                'jpg': '🖼️', 'jpeg': '🖼️', 'png': '🖼️', 'gif': '🖼️', 'svg': '🖼️',
                'pdf': '📕', 'doc': '📘', 'docx': '📘', 'zip': '📦',
                'yml': '⚙️', 'yaml': '⚙️', 'toml': '⚙️', 'ini': '⚙️',
                'sql': '🗄️', 'db': '🗄️', 'sqlite': '🗄️'
            };
            return icons[ext] || '📄';
        }

        function openFile(path) {
            const existing = openTabs.find(tab => tab.path === path);
            if (existing) {
                switchToTab(existing);
                return;
            }

            showLoading();
            fetch('/read?path=' + encodeURIComponent(path))
                .then(r => r.json())
                .then(data => {
                    hideLoading();
                    if (data.error) {
                        showNotification('Error', data.error, 'error');
                        return;
                    }

                    const tab = {
                        path: path,
                        name: data.name,
                        content: data.content,
                        modified: false
                    };

                    openTabs.push(tab);
                    renderTabs();
                    switchToTab(tab);
                    showNotification('File Opened', data.name, 'success');
                })
                .catch(err => {
                    hideLoading();
                    showNotification('Error', 'Failed to load file', 'error');
                });
        }

        function renderTabs() {
            const container = document.getElementById('tabs-container');
            container.innerHTML = '';

            openTabs.forEach(tab => {
                const tabEl = document.createElement('div');
                tabEl.className = 'tab' + (tab === activeTab ? ' active' : '') + (tab.modified ? ' modified' : '');
                tabEl.innerHTML = `
                    <span>${getFileIcon(tab.name)}</span>
                    <span class="tab-title">${tab.name}</span>
                    <span class="tab-close" onclick="event.stopPropagation(); closeTab('${tab.path}')">×</span>
                `;
                tabEl.onclick = () => switchToTab(tab);
                container.appendChild(tabEl);
            });
        }

        function switchToTab(tab) {
            activeTab = tab;
            editor.setValue(tab.content);
            
            const ext = tab.name.split('.').pop().toLowerCase();
            const modes = {
                'py': 'python', 'js': 'javascript', 'jsx': 'javascript',
                'html': 'htmlmixed', 'css': 'css', 'json': 'javascript',
                'xml': 'xml', 'sh': 'shell', 'bash': 'shell', 'md': 'markdown'
            };
            editor.setOption('mode', modes[ext] || 'text');
            
            const langNames = {
                'python': 'Python', 'javascript': 'JavaScript', 'htmlmixed': 'HTML',
                'css': 'CSS', 'xml': 'XML', 'shell': 'Shell', 'markdown': 'Markdown'
            };
            const mode = modes[ext] || 'text';
            document.getElementById('status-language').textContent = langNames[mode] || 'Plain Text';
            
            document.getElementById('editor-placeholder').style.display = 'none';
            document.getElementById('editor').style.display = 'block';
            editor.refresh();
            
            updateBreadcrumb(tab.path);
            renderTabs();
            updateFileTree();
        }

        function updateBreadcrumb(path) {
            const parts = path.split('/').filter(p => p);
            const breadcrumb = document.getElementById('breadcrumb');
            breadcrumb.innerHTML = parts.map((part, i) => {
                const partPath = '/' + parts.slice(0, i + 1).join('/');
                return `<span class="breadcrumb-item">${part}</span>` +
                    (i < parts.length - 1 ? '<span class="breadcrumb-separator">›</span>' : '');
            }).join('');
        }

        function closeTab(path) {
            const index = openTabs.findIndex(tab => tab.path === path);
            if (index === -1) return;

            const tab = openTabs[index];
            if (tab.modified && !confirm(`Do you want to save changes to ${tab.name}?`)) return;

            openTabs.splice(index, 1);

            if (tab === activeTab) {
                if (openTabs.length > 0) {
                    switchToTab(openTabs[Math.max(0, index - 1)]);
                } else {
                    activeTab = null;
                    document.getElementById('editor-placeholder').style.display = 'flex';
                    document.getElementById('editor').style.display = 'none';
                    document.getElementById('breadcrumb').innerHTML = '<span style="color: #858585;">No file selected</span>';
                }
            }

            renderTabs();
            updateFileTree();
        }

        function saveCurrentFile() {
            if (!activeTab) {
                showNotification('No File', 'No file is currently open', 'warning');
                return;
            }

            const content = editor.getValue();
            showLoading();
            
            fetch('/save', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({path: activeTab.path, content: content})
            })
            .then(r => r.json())
            .then(data => {
                hideLoading();
                if (data.success) {
                    activeTab.modified = false;
                    renderTabs();
                    updateFileTree();
                    showNotification('File Saved', `${activeTab.name} saved successfully`, 'success');
                } else {
                    showNotification('Save Failed', data.error, 'error');
                }
            })
            .catch(err => {
                hideLoading();
                showNotification('Error', 'Failed to save file', 'error');
            });
        }

        function toggleTerminal() {
            const termContainer = document.getElementById('terminal-container');
            if (termContainer.classList.contains('hidden')) {
                termContainer.classList.remove('hidden');
                if (!terminal) {
                    initTerminal();
                }
            } else {
                termContainer.classList.add('hidden');
            }
        }

        function initTerminal() {
            terminal = new Terminal({
                cols: 120,
                rows: 15,
                theme: {
                    background: '#1e1e1e',
                    foreground: '#cccccc',
                    cursor: '#ffffff',
                    black: '#000000',
                    red: '#cd3131',
                    green: '#0dbc79',
                    yellow: '#e5e510',
                    blue: '#2472c8',
                    magenta: '#bc3fbc',
                    cyan: '#11a8cd',
                    white: '#e5e5e5',
                    brightBlack: '#666666',
                    brightRed: '#f14c4c',
                    brightGreen: '#23d18b',
                    brightYellow: '#f5f543',
                    brightBlue: '#3b8eea',
                    brightMagenta: '#d670d6',
                    brightCyan: '#29b8db',
                    brightWhite: '#e5e5e5'
                }
            });
            
            terminal.open(document.getElementById('terminal-body'));
            
            fetch('/init').then(r => r.json()).then(data => {
                currentDir = data.cwd;
                username = data.username;
                hostname = data.hostname;
                terminal.write('\\x1b[1;36mVSCode Web Terminal\\x1b[0m\\r\\n');
                terminal.write(getPrompt());
            });
            
            terminal.onData(e => {
                switch(e) {
                    case '\\r':
                        terminal.write('\\r\\n');
                        if (commandBuffer.trim()) {
                            executeCommand(commandBuffer.trim());
                        } else {
                            terminal.write(getPrompt());
                        }
                        commandBuffer = '';
                        break;
                    case '\\u007F':
                        if (commandBuffer.length > 0) {
                            commandBuffer = commandBuffer.slice(0, -1);
                            terminal.write('\\b \\b');
                        }
                        break;
                    case '\\u0003':
                        terminal.write('^C\\r\\n' + getPrompt());
                        commandBuffer = '';
                        break;
                    default:
                        if (e >= String.fromCharCode(0x20) && e <= String.fromCharCode(0x7E)) {
                            commandBuffer += e;
                            terminal.write(e);
                        }
                }
            });
        }

        function getPrompt() {
            let shortDir = currentDir;
            if (currentDir.startsWith('/home/' + username)) {
                shortDir = '~' + currentDir.substring(('/home/' + username).length);
            }
            return `\\x1b[1;32m${username}@${hostname}\\x1b[0m:\\x1b[1;34m${shortDir}\\x1b[0m$ `;
        }

        function executeCommand(cmd) {
            fetch('/exec', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({cmd: cmd, cwd: currentDir})
            })
            .then(r => r.json())
            .then(data => {
                if (data.cwd) currentDir = data.cwd;
                if (data.output) {
                    terminal.write(data.output.replace(/\\n/g, '\\r\\n'));
                    if (!data.output.endsWith('\\n')) terminal.write('\\r\\n');
                }
                terminal.write(getPrompt());
            })
            .catch(err => {
                terminal.write('\\x1b[1;31mError: ' + err + '\\x1b[0m\\r\\n' + getPrompt());
            });
        }

        function clearTerminal() {
            if (terminal) {
                terminal.clear();
                terminal.write(getPrompt());
            }
        }

        function splitTerminal() {
            showNotification('Terminal Split', 'Terminal split coming soon!', 'info');
        }

        function initTerminalResize() {
            const handle = document.getElementById('terminal-resize');
            const termContainer = document.getElementById('terminal-container');
            let isResizing = false;
            let startY = 0;
            let startHeight = 0;

            handle.addEventListener('mousedown', (e) => {
                isResizing = true;
                startY = e.clientY;
                startHeight = termContainer.offsetHeight;
                document.body.style.cursor = 'ns-resize';
            });

            document.addEventListener('mousemove', (e) => {
                if (!isResizing) return;
                const delta = startY - e.clientY;
                const newHeight = Math.min(Math.max(startHeight + delta, 100), 600);
                termContainer.style.height = newHeight + 'px';
            });

            document.addEventListener('mouseup', () => {
                if (isResizing) {
                    isResizing = false;
                    document.body.style.cursor = 'default';
                }
            });
        }

        function toggleSidebar(type) {
            const sidebar = document.getElementById('sidebar');
            const sidebarTitle = document.getElementById('sidebar-title');
            
            if (type) {
                currentSidebar = type;
                
                document.querySelectorAll('.activity-icon').forEach(icon => {
                    icon.classList.remove('active');
                });
                event.currentTarget.classList.add('active');
                
                if (sidebar.classList.contains('collapsed')) {
                    sidebar.classList.remove('collapsed');
                }
                
                if (type === 'explorer') {
                    sidebarTitle.textContent = 'EXPLORER';
                } else if (type === 'search') {
                    sidebarTitle.textContent = 'SEARCH';
                    showNotification('Search', 'Search functionality coming soon!', 'info');
                } else if (type === 'git') {
                    sidebarTitle.textContent = 'SOURCE CONTROL';
                    showNotification('Git', 'Source control coming soon!', 'info');
                }
            } else {
                sidebar.classList.toggle('collapsed');
            }
        }

        function toggleFolderSection(header) {
            const section = header.parentElement;
            section.classList.toggle('collapsed');
        }

        function createNewFile() {
            const name = prompt('Enter file name:');
            if (name) {
                showNotification('Create File', `Creating ${name}...`, 'info');
            }
        }

        function createNewFolder() {
            const name = prompt('Enter folder name:');
            if (name) {
                showNotification('Create Folder', `Creating ${name}...`, 'info');
            }
        }

        function refreshExplorer() {
            loadDirectory('/');
            showNotification('Explorer', 'Refreshed successfully', 'success');
        }

        function renameFile() {
            if (!activeTab) return;
            const newName = prompt('Enter new name:', activeTab.name);
            if (newName) {
                showNotification('Rename', 'Rename functionality coming soon!', 'info');
            }
        }

        function showSettings() {
            showNotification('Settings', 'Settings panel coming soon!', 'info');
        }

        function toggleCommandPalette() {
            const palette = document.getElementById('command-palette');
            palette.classList.toggle('visible');
            
            if (palette.classList.contains('visible')) {
                document.getElementById('command-input').focus();
                populateCommands();
            }
        }

        function toggleQuickOpen() {
            showNotification('Quick Open', 'Quick file open coming soon!', 'info');
        }

        function populateCommands() {
            const commands = [
                { icon: '💾', text: 'File: Save', shortcut: 'Ctrl+S', action: saveCurrentFile },
                { icon: '📄', text: 'File: New File', shortcut: '', action: createNewFile },
                { icon: '🔄', text: 'File: Refresh Explorer', shortcut: '', action: refreshExplorer },
                { icon: '⌨️', text: 'View: Toggle Terminal', shortcut: 'Ctrl+`', action: toggleTerminal },
                { icon: '📂', text: 'View: Toggle Sidebar', shortcut: 'Ctrl+B', action: () => toggleSidebar() },
                { icon: '🗑️', text: 'Terminal: Clear', shortcut: '', action: clearTerminal }
            ];

            const list = document.getElementById('command-list');
            list.innerHTML = commands.map((cmd, i) => `
                <div class="command-item ${i === 0 ? 'selected' : ''}" onclick="executeCommandPaletteAction(${i})">
                    <span class="command-item-icon">${cmd.icon}</span>
                    <span class="command-item-text">${cmd.text}</span>
                    <span class="command-item-shortcut">${cmd.shortcut}</span>
                </div>
            `).join('');

            window.commandPaletteActions = commands;
        }

        function executeCommandPaletteAction(index) {
            const action = window.commandPaletteActions[index].action;
            if (action) action();
            hideCommandPalette();
        }

        function hideCommandPalette() {
            document.getElementById('command-palette').classList.remove('visible');
        }

        function showContextMenu(x, y) {
            const menu = document.getElementById('context-menu');
            menu.style.display = 'block';
            menu.style.left = x + 'px';
            menu.style.top = y + 'px';
        }

        function hideContextMenu() {
            document.getElementById('context-menu').style.display = 'none';
        }

        function contextAction(action) {
            hideContextMenu();
            
            switch(action) {
                case 'cut':
                case 'copy':
                case 'paste':
                    document.execCommand(action);
                    break;
                case 'rename':
                    renameFile();
                    break;
                case 'delete':
                    if (activeTab && confirm(`Delete ${activeTab.name}?`)) {
                        showNotification('Delete', 'Delete functionality coming soon!', 'info');
                    }
                    break;
            }
        }

        function showNotification(title, message, type = 'info') {
            const icons = {
                success: '✓',
                error: '✕',
                warning: '⚠',
                info: 'ℹ'
            };

            const notification = document.createElement('div');
            notification.className = 'notification';
            notification.innerHTML = `
                <div class="notification-icon">${icons[type]}</div>
                <div class="notification-content">
                    <div class="notification-title">${title}</div>
                    <div class="notification-message">${message}</div>
                </div>
                <div class="notification-close" onclick="this.parentElement.remove()">×</div>
            `;
            
            document.body.appendChild(notification);
            
            setTimeout(() => {
                notification.remove();
            }, 4000);
        }

        function showLoading() {
            document.getElementById('loading').classList.add('visible');
        }

        function hideLoading() {
            document.getElementById('loading').classList.remove('visible');
        }
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/list')
def list_directory():
    try:
        path = request.args.get('path', '/')
        if not os.path.exists(path):
            return jsonify({'error': 'Path does not exist'})
        
        folders = []
        files = []
        
        for item in os.listdir(path):
            if item.startswith('.'):
                continue
            
            full_path = os.path.join(path, item)
            
            if os.path.isdir(full_path):
                folders.append({'name': item, 'path': full_path})
            else:
                files.append({'name': item, 'path': full_path})
        
        folders.sort(key=lambda x: x['name'].lower())
        files.sort(key=lambda x: x['name'].lower())
        
        return jsonify({'folders': folders, 'files': files})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/read')
def read_file():
    try:
        path = request.args.get('path', '')
        if not os.path.exists(path):
            return jsonify({'error': 'File does not exist'})
        
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        return jsonify({
            'name': os.path.basename(path),
            'content': content
        })
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/save', methods=['POST'])
def save_file():
    try:
        data = request.json
        path = data.get('path')
        content = data.get('content')
        
        if not path:
            return jsonify({'success': False, 'error': 'No path provided'})
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/init')
def init_terminal():
    try:
        cwd = os.getcwd()
        username = pwd.getpwuid(os.getuid()).pw_name
        hostname = os.uname().nodename
        
        return jsonify({
            'cwd': cwd,
            'username': username,
            'hostname': hostname
        })
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/exec', methods=['POST'])
def execute_command():
    try:
        data = request.json
        cmd = data.get('cmd', '')
        cwd = data.get('cwd', os.getcwd())
        
        if cmd.startswith('cd '):
            new_dir = cmd[3:].strip()
            if new_dir == '~':
                new_dir = os.path.expanduser('~')
            elif not os.path.isabs(new_dir):
                new_dir = os.path.join(cwd, new_dir)
            
            if os.path.isdir(new_dir):
                cwd = os.path.abspath(new_dir)
                return jsonify({'output': '', 'cwd': cwd})
            else:
                return jsonify({'output': f'cd: {new_dir}: No such file or directory\n', 'cwd': cwd})
        
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        output = result.stdout + result.stderr
        
        return jsonify({
            'output': output,
            'cwd': cwd
        })
    except subprocess.TimeoutExpired:
        return jsonify({'output': 'Command timed out\n', 'cwd': cwd})
    except Exception as e:
        return jsonify({'output': f'Error: {str(e)}\n', 'cwd': cwd})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=6534, debug=True)
