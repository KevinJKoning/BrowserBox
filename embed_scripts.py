#!/usr/bin/env python3
"""
Script to embed Python scripts into BrowserBox.html as base64-encoded data.
This creates a self-contained version of BrowserBox with pre-loaded Python scripts.
"""

import os
import base64
import json
from pathlib import Path

def parse_required_files(script_content):
    """Parse magic comments for user_files and process_files."""
    import re
    
    user_files_regex = r'#\s*user_files:\s*(.*)'
    process_files_regex = r'#\s*process_files:\s*(.*)'
    
    user_files_match = re.search(user_files_regex, script_content, re.IGNORECASE)
    process_files_match = re.search(process_files_regex, script_content, re.IGNORECASE)
    
    user_files = []
    if user_files_match and user_files_match.group(1):
        user_files = [f.strip() for f in user_files_match.group(1).split(',') if f.strip()]
    
    process_files = []
    if process_files_match and process_files_match.group(1):
        process_files = [f.strip() for f in process_files_match.group(1).split(',') if f.strip()]
    
    return user_files, process_files

def collect_python_scripts(directory='.'):
    """Collect all Python scripts from the current directory."""
    scripts = []
    
    for file_path in Path(directory).glob('*.py'):
        if file_path.name == 'embed_scripts.py':  # Skip this script itself
            continue
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse magic comments
            user_files, process_files = parse_required_files(content)
            
            # Encode content as base64
            content_b64 = base64.b64encode(content.encode('utf-8')).decode('ascii')
            
            script_info = {
                'name': file_path.name,
                'content_b64': content_b64,
                'userFiles': user_files,
                'processFiles': process_files
            }
            
            scripts.append(script_info)
            print(f"Collected: {file_path.name} (user_files: {user_files}, process_files: {process_files})")
            
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
    
    return scripts

def create_embedded_browserbox(scripts, input_file='BrowserBox.html', output_file='BrowserBox_with_scripts.html'):
    """Create a new BrowserBox.html with embedded Python scripts."""
    
    # Read the original BrowserBox.html
    with open(input_file, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Create the embedded scripts data as JavaScript
    scripts_js = f"const embeddedScripts = {json.dumps(scripts, indent=8)};"
    
    # Create the base64 decoder function
    decoder_function = '''
        // Function to decode base64 embedded scripts
        function loadEmbeddedScripts() {
            if (typeof embeddedScripts === 'undefined' || embeddedScripts.length === 0) {
                return;
            }
            
            log(`Loading ${embeddedScripts.length} embedded Python script(s)...`);
            
            embeddedScripts.forEach(scriptData => {
                try {
                    // Decode base64 content
                    const content = atob(scriptData.content_b64);
                    
                    // Create a File-like object for the script
                    const blob = new Blob([content], { type: 'text/plain' });
                    const file = new File([blob], scriptData.name, { 
                        lastModified: new Date().getTime() 
                    });
                    
                    // Add to pythonScripts array if not already present
                    if (!pythonScripts.some(ps => ps.name === scriptData.name)) {
                        const newScript = {
                            name: scriptData.name,
                            content: content,
                            userFiles: scriptData.userFiles || [],
                            processFiles: scriptData.processFiles || [],
                            fileObject: file,
                            id: `py-${scriptData.name.replace(/[^a-zA-Z0-9]/g, '-')}`
                        };
                        pythonScripts.push(newScript);
                        log(`Loaded embedded script: ${scriptData.name} (User files: ${newScript.userFiles.join(', ') || 'none'}, Process files: ${newScript.processFiles.join(', ') || 'none'})`);
                    }
                } catch (error) {
                    log(`Error loading embedded script ${scriptData.name}: ${error.message}`, 'error');
                }
            });
            
            // Sort scripts and update UI
            pythonScripts.sort((a, b) => a.name.localeCompare(b.name));
            updateScriptsList();
            updateFileDropZone();
            updateRunButtonState();
            
            // Hide script zone instructions since we have scripts
            const scriptZoneInstructions = document.getElementById('scriptZoneInstructions');
            if (scriptZoneInstructions) {
                scriptZoneInstructions.style.display = 'none';
            }
        }'''
    
    # Find the init() function and add our loader call
    init_function_pattern = r'(function init\(\) {[^}]*)(log\(\'App initialized and ready\'\);)'
    
    def replace_init(match):
        before_log = match.group(1)
        log_line = match.group(2)
        return f"{before_log}loadEmbeddedScripts();\n            {log_line}"
    
    # Insert the embedded scripts data and decoder function before the closing </script> tag
    # Find the main script section (the last one before </body>)
    script_end_pattern = r'(        // Start the app\s+init\(\);\s+)(    </script>)'
    
    def insert_embedded_code(match):
        before_script_end = match.group(1)
        script_closing = match.group(2)
        
        return f'''        // Embedded Python Scripts Data
        {scripts_js}

{decoder_function}

        {before_script_end}{script_closing}'''
    
    # Apply the modifications
    html_content = re.sub(script_end_pattern, insert_embedded_code, html_content, flags=re.MULTILINE | re.DOTALL)
    html_content = re.sub(init_function_pattern, replace_init, html_content)
    
    # Write the new file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"Created {output_file} with {len(scripts)} embedded Python scripts")
    return output_file

def main():
    """Main function to embed scripts into BrowserBox.html."""
    
    # Check if BrowserBox.html exists
    if not os.path.exists('BrowserBox.html'):
        print("Error: BrowserBox.html not found in current directory")
        return
    
    # Collect Python scripts from current directory
    scripts = collect_python_scripts()
    
    if not scripts:
        print("No Python scripts found to embed")
        return
    
    # Create embedded version
    output_file = create_embedded_browserbox(scripts)
    
    print(f"\nSuccess! Created {output_file} with embedded scripts:")
    for script in scripts:
        print(f"  - {script['name']}")
    
    print(f"\nYou can now open {output_file} in a web browser and the Python scripts will be pre-loaded.")

if __name__ == '__main__':
    import re
    main()