cat << 'EOF' > app.py
from flask import Flask, render_template_string, request, jsonify
import os
import subprocess
import pwd

app = Flask(__name__)

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Modern File Explorer + Terminal</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.2/codemirror.min.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.2/theme/monokai.min.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.2/theme/eclipse.min.css">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/xterm@4.19.0/css/xterm.css" />
    <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.2/codemirror.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.2/mode/python/python.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.2/mode/javascript/javascript.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.2/mode/css/css.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.2/mode/htmlmixed/htmlmixed.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.2/mode/xml/xml.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.2/mode/shell/shell.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.2/mode/markdown/markdown.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/xterm@4.19.0/lib/xterm.js"></script>
    <style>
        :root {
            --bg-light: #f4f4f5; --bg-sidebar: #ffffff; --bg-main: #ffffff;
            --bg-hover: #e2e2e2; --text-primary: #1f2937; --text-secondary: #4b5563;
            --accent: #3b82f6; --accent-hover: #2563eb; --shadow: rgba(0,0,0,0.1); --radius: 8px;
        }
        body.dark {
            --bg-light: #1f2937; --bg-sidebar: #111827; --bg-main: #1f2937;
            --bg-hover: #374151; --text-primary: #f9fafb; --text-secondary: #9ca3af;
            --accent: #3b82f6; --accent-hover: #2563eb; --shadow: rgba(0,0,0,0.4);
        }
        *{margin:0;padding:0;box-sizing:border-box;font-family:'Segoe UI',sans-serif;}
        body{display:flex;height:100vh;background:var(--bg-light);color:var(--text-primary);transition:0.3s;}
        #sidebar{width:300px;background:var(--bg-sidebar);display:flex;flex-direction:column;box-shadow:2px 0 5px var(--shadow);}
        #header{padding:16px;font-weight:600;font-size:18px;display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid var(--bg-hover);}
        #file-input-container{padding:8px 16px;display:flex;gap:6px;border-bottom:1px solid var(--bg-hover);}
        #path-input{flex:1;padding:6px 10px;border-radius:var(--radius);border:1px solid var(--bg-hover);background:var(--bg-light);color:var(--text-primary);}
        #file-list{flex:1;overflow-y:auto;padding:8px 0;}
        .folder, .file{padding:10px 16px;cursor:pointer;transition:0.2s;display:flex;align-items:center;border-radius:var(--radius);margin:2px 8px;}
        .folder:hover, .file:hover{background:var(--bg-hover);}
        .folder::before{content:"📁";margin-right:8px;}
        .file::before{content:"📄";margin-right:8px;}
        .parent-folder::before{content:"⬆️";margin-right:8px;}
        #main{flex:1;display:flex;flex-direction:column;background:var(--bg-main);}
        #toolbar{padding:10px 16px;display:flex;align-items:center;gap:10px;border-bottom:1px solid var(--bg-hover);background:var(--bg-light);}
        #filename{flex:1;font-weight:600;}
        button{padding:6px 12px;border:none;border-radius:var(--radius);cursor:pointer;background:var(--accent);color:#fff;transition:0.2s;}
        button:hover{background:var(--accent-hover);}
        #editor-container{flex:1;overflow:hidden;display:flex;flex-direction:column;padding:10px;}
        .CodeMirror{flex:1;height:100%;font-size:14px;border-radius:var(--radius);overflow:auto;}
        #terminal-container{position:absolute;bottom:0;left:300px;right:0;height:300px;background:#0c0c0c;display:none;border-top:2px solid var(--accent);z-index:100;}
        .terminal{height:100%;padding:10px;}
    </style>
</head>
<body>
    <div id="sidebar">
        <div id="header">
            <span>📂 Explorer</span>
            <button onclick="toggleTheme()">🌙</button>
        </div>
        <div id="file-input-container">
            <input type="text" id="path-input" placeholder="Enter path">
            <button onclick="goToPath()">Go</button>
        </div>
        <div id="file-list"></div>
    </div>
    <div id="main">
        <div id="toolbar">
            <span id="filename">Select a file</span>
            <button onclick="saveFile()" id="save-btn" style="display:none;">💾 Save</button>
            <button onclick="toggleTerminal()">🖥️ Terminal</button>
        </div>
        <div id="editor-container">
            <textarea id="editor"></textarea>
        </div>
    </div>
    <div id="terminal-container"></div>

<script>
let editor = CodeMirror.fromTextArea(document.getElementById('editor'), {lineNumbers:true, theme:'eclipse', mode:'python', lineWrapping:true});
let currentFile=null;
let darkMode=false;
let terminal=null;
let commandBuffer='';
let currentDir='';
let username='';
let hostname='';

// Theme toggle
function toggleTheme(){darkMode=!darkMode;document.body.classList.toggle('dark');editor.setOption('theme',darkMode?'monokai':'eclipse');}

// File explorer functions
function loadDirectory(path){fetch('/list?path='+encodeURIComponent(path)).then(r=>r.json()).then(data=>{if(data.error){alert(data.error);return;}document.getElementById('path-input').value=data.path;let html='';if(data.parent){html+=`<div class="folder parent-folder" onclick="loadDirectory('${data.parent.replace(/'/g,"\\'")}')">..</div>`;}data.folders.forEach(f=>{html+=`<div class="folder" onclick="loadDirectory('${f.path.replace(/'/g,"\\'")}')">${f.name}</div>`;});data.files.forEach(f=>{html+=`<div class="file" onclick="loadFile('${f.path.replace(/'/g,"\\'")}')">${f.name}</div>`;});document.getElementById('file-list').innerHTML=html;});}
function goToPath(){loadDirectory(document.getElementById('path-input').value);}
function loadFile(path){fetch('/read?path='+encodeURIComponent(path)).then(r=>r.json()).then(data=>{if(data.error){alert(data.error);return;}currentFile=path;editor.setValue(data.content);document.getElementById('filename').textContent='📄 '+data.name;document.getElementById('save-btn').style.display='block';let ext=path.split('.').pop().toLowerCase();let mode={'py':'python','js':'javascript','html':'htmlmixed','css':'css','json':'javascript','xml':'xml','sh':'shell','md':'markdown'}[ext]||'text';editor.setOption('mode',mode);});}
function saveFile(){if(!currentFile) return;fetch('/save',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({path:currentFile,content:editor.getValue()})}).then(r=>r.json()).then(data=>{if(data.success){alert('Saved ✅');}else{alert('Error: '+data.error);}});}

// Terminal functions
function getPrompt(){
    let shortDir = currentDir;
    if(currentDir.startsWith('/home/'+username)){
        shortDir = '~' + currentDir.substring(('/home/'+username).length);
    }
    return `\\x1b[1;32m${username}@${hostname}\\x1b[0m:\\x1b[1;34m${shortDir}\\x1b[0m$ `;
}

function toggleTerminal(){
    let termDiv=document.getElementById('terminal-container');
    if(termDiv.style.display==='none' || termDiv.style.display===''){
        termDiv.style.display='block';
        if(!terminal){
            terminal = new Terminal({
                cols:120,
                rows:15,
                theme:{
                    background:'#0c0c0c',
                    foreground:'#cccccc',
                    cursor:'#ffffff',
                    selection:'rgba(255, 255, 255, 0.3)',
                    black:'#0c0c0c',
                    red:'#c50f1f',
                    green:'#13a10e',
                    yellow:'#c19c00',
                    blue:'#0037da',
                    magenta:'#881798',
                    cyan:'#3a96dd',
                    white:'#cccccc',
                    brightBlack:'#767676',
                    brightRed:'#e74856',
                    brightGreen:'#16c60c',
                    brightYellow:'#f9f1a5',
                    brightBlue:'#3b78ff',
                    brightMagenta:'#b4009e',
                    brightCyan:'#61d6d6',
                    brightWhite:'#f2f2f2'
                }
            });
            terminal.open(termDiv);
            
            // Initialize terminal
            fetch('/init').then(r=>r.json()).then(data=>{
                currentDir=data.cwd;
                username=data.username;
                hostname=data.hostname;
                terminal.write('Web Terminal - Press Ctrl+J to toggle\\r\\n');
                terminal.write(getPrompt());
            });
            
            terminal.onData(e=>{
                switch(e){
                    case '\\r': // Enter
                        terminal.write('\\r\\n');
                        if(commandBuffer.trim()){
                            executeCommand(commandBuffer.trim());
                        }else{
                            terminal.write(getPrompt());
                        }
                        commandBuffer='';
                        break;
                    case '\\u007F': // Backspace
                        if(commandBuffer.length>0){
                            commandBuffer=commandBuffer.slice(0,-1);
                            terminal.write('\\b \\b');
                        }
                        break;
                    case '\\u0003': // Ctrl+C
                        terminal.write('^C\\r\\n'+getPrompt());
                        commandBuffer='';
                        break;
                    case '\\t': // Tab (autocomplete disabled for simplicity)
                        break;
                    default:
                        if(e>=String.fromCharCode(0x20) && e<=String.fromCharCode(0x7E)){
                            commandBuffer+=e;
                            terminal.write(e);
                        }
                }
            });
        }
    }else{
        termDiv.style.display='none';
    }
}

function executeCommand(cmd){
    fetch('/exec',{
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify({cmd:cmd, cwd:currentDir})
    })
    .then(r=>r.json())
    .then(data=>{
        if(data.cwd){
            currentDir=data.cwd;
        }
        if(data.output){
            terminal.write(data.output.replace(/\\n/g,'\\r\\n'));
            if(!data.output.endsWith('\\n')){
                terminal.write('\\r\\n');
            }
        }
        terminal.write(getPrompt());
    })
    .catch(err=>{
        terminal.write('Error: '+err+'\\r\\n'+getPrompt());
    });
}

// Keyboard shortcut Ctrl+J
document.addEventListener('keydown', e=>{
    if(e.ctrlKey && e.key.toLowerCase()==='j'){
        e.preventDefault();
        toggleTerminal();
    }
});

loadDirectory('/');
</script>
</body>
</html>
'''

@app.route('/')
def index(): 
    return render_template_string(HTML_TEMPLATE)

@app.route('/init')
def init_terminal():
    try:
        cwd = os.getcwd()
        username = pwd.getpwuid(os.getuid()).pw_name
        hostname = os.uname().nodename
        return jsonify({'cwd': cwd, 'username': username, 'hostname': hostname})
    except:
        return jsonify({'cwd': '/home/container', 'username': 'user', 'hostname': 'server'})

@app.route('/list')
def list_directory():
    req_path=request.args.get('path','/')
    path=os.path.abspath(req_path)
    try:
        items=os.listdir(path)
        folders,files=[],[]
        for item in sorted(items):
            item_path=os.path.join(path,item)
            if os.path.isdir(item_path): folders.append({'name':item,'path':item_path})
            elif os.path.isfile(item_path): files.append({'name':item,'path':item_path})
        parent=os.path.dirname(path) if path!='/' else None
        return jsonify({'path':path,'parent':parent,'folders':folders,'files':files})
    except Exception as e: return jsonify({'error':str(e)})

@app.route('/read')
def read_file():
    req_path=request.args.get('path','')
    try:
        path=os.path.abspath(req_path)
        with open(path,'r',encoding='utf-8') as f: content=f.read()
        return jsonify({'content':content,'name':os.path.basename(path)})
    except UnicodeDecodeError: return jsonify({'error':'Binary file'}),400
    except Exception as e: return jsonify({'error':str(e)})

@app.route('/save',methods=['POST'])
def save_file():
    data=request.json
    try:
        path=os.path.abspath(data.get('path',''))
        with open(path,'w',encoding='utf-8') as f: f.write(data.get('content',''))
        return jsonify({'success':True})
    except Exception as e: return jsonify({'error':str(e)})

@app.route('/exec',methods=['POST'])
def exec_command():
    data=request.json
    try:
        cmd=data.get('cmd','').strip()
        cwd=data.get('cwd',os.getcwd())
        
        if not cmd:
            return jsonify({'output':'', 'cwd':cwd})
        
        # Handle cd command specially
        if cmd.startswith('cd '):
            new_dir = cmd[3:].strip()
            if new_dir == '~':
                new_dir = os.path.expanduser('~')
            elif not os.path.isabs(new_dir):
                new_dir = os.path.join(cwd, new_dir)
            
            new_dir = os.path.abspath(new_dir)
            
            if os.path.isdir(new_dir):
                return jsonify({'output':'', 'cwd':new_dir})
            else:
                return jsonify({'output':f'cd: {new_dir}: No such file or directory', 'cwd':cwd})
        elif cmd == 'cd':
            return jsonify({'output':'', 'cwd':os.path.expanduser('~')})
        
        # Execute other commands
        result=subprocess.run(
            cmd, 
            shell=True, 
            capture_output=True, 
            text=True, 
            timeout=30,
            cwd=cwd
        )
        output=result.stdout + result.stderr
        return jsonify({'output':output if output else '', 'cwd':cwd})
        
    except subprocess.TimeoutExpired:
        return jsonify({'output':'Command timeout (30s)', 'cwd':cwd})
    except Exception as e:
        return jsonify({'output':f'Error: {str(e)}', 'cwd':cwd})

if __name__=='__main__': 
    app.run(host='0.0.0.0',port=6534,debug=False)
EOF

python app.py
