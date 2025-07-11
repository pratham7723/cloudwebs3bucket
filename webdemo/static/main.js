document.addEventListener('DOMContentLoaded', function() {
    // Upload
    const uploadForm = document.getElementById('uploadForm');
    const fileInput = document.getElementById('fileInput');
    const folderDropdown = document.getElementById('folderDropdown');
    const uploadResult = document.getElementById('uploadResult');

    // Populate folder dropdown
    function loadFolders() {
        fetch('/api/list-folders')
            .then(res => res.json())
            .then(data => {
                folderDropdown.innerHTML = '';
                const defaultOpt = document.createElement('option');
                defaultOpt.value = '';
                defaultOpt.textContent = '-- Select folder --';
                folderDropdown.appendChild(defaultOpt);
                if (data.folders && data.folders.length) {
                    data.folders.forEach(f => {
                        const opt = document.createElement('option');
                        opt.value = f;
                        opt.textContent = f;
                        folderDropdown.appendChild(opt);
                    });
                }
            });
    }
    loadFolders();

    uploadForm.addEventListener('submit', function(e) {
        e.preventDefault();
        const formData = new FormData();
        formData.append('file', fileInput.files[0]);
        let folder = folderDropdown.value;
        if (folder) formData.append('folder', folder);
        fetch('/api/upload', {
            method: 'POST',
            body: formData
        })
        .then(res => res.json())
        .then(data => {
            uploadResult.style.display = '';
            if (data.success) {
                uploadResult.textContent = 'Uploaded: ' + data.filename;
                uploadResult.className = 'alert';
                loadFiles();
                loadFolders();
            } else {
                uploadResult.textContent = 'Error: ' + data.error;
                uploadResult.className = 'alert alert-error';
            }
            setTimeout(() => { uploadResult.style.display = 'none'; }, 3500);
        })
        .catch(err => {
            uploadResult.textContent = 'Error: ' + err;
            uploadResult.className = 'alert alert-error';
            uploadResult.style.display = '';
            setTimeout(() => { uploadResult.style.display = 'none'; }, 3500);
        });
    });

    // Helper: Build tree from flat file list
    function buildTree(files) {
        const root = {};
        files.forEach(path => {
            const parts = path.split('/');
            let node = root;
            for (let i = 0; i < parts.length; i++) {
                const part = parts[i];
                if (!node[part]) {
                    node[part] = (i === parts.length - 1) ? null : {};
                }
                node = node[part];
            }
        });
        return root;
    }

    // Helper: Get file icon by extension
    function getFileIcon(filename) {
        const ext = filename.split('.').pop().toLowerCase();
        if (["jpg","jpeg","png","gif","bmp","webp"].includes(ext)) return '🖼️';
        if (["pdf"].includes(ext)) return '📄';
        if (["txt","md","log","csv"].includes(ext)) return '📑';
        if (["zip","tar","gz","rar"].includes(ext)) return '🗜️';
        if (["doc","docx"].includes(ext)) return '📃';
        if (["xls","xlsx"].includes(ext)) return '📊';
        if (["ppt","pptx"].includes(ext)) return '📈';
        if (["py","js","html","css","json"].includes(ext)) return '💻';
        return '📄';
    }

    // Helper: Render tree as nested list (no preview)
    function renderTree(node, parentPath = '') {
        const ul = document.createElement('ul');
        for (const key in node) {
            const fullPath = parentPath ? parentPath + '/' + key : key;
            const li = document.createElement('li');
            if (node[key] && typeof node[key] === 'object') {
                // Folder
                const folderSpan = document.createElement('span');
                folderSpan.innerHTML = '📁 <b>' + key + '</b>';
                folderSpan.className = 'folder';
                folderSpan.onclick = function() {
                    const childUl = li.querySelector('ul');
                    if (childUl.style.display === 'none') {
                        childUl.style.display = '';
                        folderSpan.innerHTML = '📂 <b>' + key + '</b>';
                    } else {
                        childUl.style.display = 'none';
                        folderSpan.innerHTML = '📁 <b>' + key + '</b>';
                    }
                };
                li.appendChild(folderSpan);
                const childUl = renderTree(node[key], fullPath);
                childUl.style.display = 'none';
                li.appendChild(childUl);
            } else {
                // File
                li.innerHTML = getFileIcon(key) + ' ' + key;
                // Download button
                const downloadBtn = document.createElement('button');
                downloadBtn.textContent = 'Download';
                downloadBtn.onclick = function() {
                    window.open('/api/download?key=' + encodeURIComponent(fullPath) + '&download=1', '_blank');
                };
                li.appendChild(downloadBtn);
                // Delete button
                const deleteBtn = document.createElement('button');
                deleteBtn.textContent = 'Delete';
                deleteBtn.onclick = function() {
                    if (confirm('Delete ' + fullPath + '?')) {
                        fetch('/api/delete-file', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ key: fullPath })
                        })
                        .then(res => res.json())
                        .then(data => {
                            if (data.success) {
                                loadFiles();
                                loadFolders();
                            } else {
                                alert('Error: ' + data.error);
                            }
                        });
                    }
                };
                li.appendChild(deleteBtn);
                // Edit button for text files
                if (key.match(/\.(txt|md|csv|log|json|py|js|html|css)$/i)) {
                    const editBtn = document.createElement('button');
                    editBtn.textContent = 'Edit';
                    editBtn.onclick = function() { openEdit(fullPath); };
                    li.appendChild(editBtn);
                }
                // Version history button
                const versionBtn = document.createElement('button');
                versionBtn.textContent = 'Versions';
                versionBtn.onclick = function() { showVersions(fullPath, key); };
                li.appendChild(versionBtn);
            }
            ul.appendChild(li);
        }
        return ul;
    }

    // List files
    function loadFiles() {
        fetch('/api/list-files')
            .then(res => res.json())
            .then(data => {
                const fileList = document.getElementById('fileList');
                fileList.innerHTML = '';
                if (data.files && data.files.length) {
                    const tree = buildTree(data.files);
                    const treeUl = renderTree(tree);
                    fileList.appendChild(treeUl);
                } else {
                    fileList.innerHTML = '<li>No files found.</li>';
                }
            });
    }
    loadFiles();

    // Show logs
    function loadLogs() {
        fetch('/api/logs')
            .then(res => res.json())
            .then(data => {
                document.getElementById('logContent').textContent = data.log || data.error || '';
            });
    }
    loadLogs();

    // Show versioning status
    function loadVersioning() {
        fetch('/api/versioning')
            .then(res => res.json())
            .then(data => {
                document.getElementById('versioningStatus').textContent = data.versioning || data.error || '';
            });
    }
    loadVersioning();

    // Edit logic
    const editSection = document.getElementById('editSection');
    const editFileName = document.getElementById('editFileName');
    const editFileContent = document.getElementById('editFileContent');
    const saveEditBtn = document.getElementById('saveEditBtn');
    const cancelEditBtn = document.getElementById('cancelEditBtn');
    const editResult = document.getElementById('editResult');
    let currentEditKey = null;

    function openEdit(key) {
        fetch('/api/get-file?key=' + encodeURIComponent(key))
            .then(res => res.json())
            .then(data => {
                if (data.content !== undefined) {
                    editFileName.textContent = key;
                    editFileContent.value = data.content;
                    editSection.style.display = '';
                    editResult.textContent = '';
                    editResult.style.display = 'none';
                    currentEditKey = key;
                } else {
                    alert('Error: ' + (data.error || 'Unable to fetch file.'));
                }
            });
    }

    saveEditBtn.onclick = function() {
        fetch('/api/edit-file', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ key: currentEditKey, content: editFileContent.value })
        })
        .then(res => res.json())
        .then(data => {
            editResult.style.display = '';
            if (data.success) {
                editResult.textContent = 'Saved!';
                editResult.className = 'alert';
                loadFiles();
            } else {
                editResult.textContent = 'Error: ' + data.error;
                editResult.className = 'alert alert-error';
            }
            setTimeout(() => { editResult.style.display = 'none'; }, 3000);
        });
    };

    cancelEditBtn.onclick = function() {
        editSection.style.display = 'none';
        editFileName.textContent = '';
        editFileContent.value = '';
        editResult.textContent = '';
        editResult.style.display = 'none';
        currentEditKey = null;
    };

    // Version history modal/section (with restore)
    let versionModal = document.getElementById('versionModal');
    if (!versionModal) {
        versionModal = document.createElement('div');
        versionModal.id = 'versionModal';
        versionModal.style.display = 'none';
        versionModal.style.position = 'fixed';
        versionModal.style.top = '0';
        versionModal.style.left = '0';
        versionModal.style.width = '100vw';
        versionModal.style.height = '100vh';
        versionModal.style.background = 'rgba(0,0,0,0.4)';
        versionModal.style.zIndex = '1000';
        versionModal.innerHTML = '<div id="versionModalContent" style="background:#fff;max-width:600px;margin:60px auto;padding:20px;border-radius:8px;position:relative;"></div>';
        document.body.appendChild(versionModal);
    }
    function showVersions(key, displayName) {
        fetch('/api/list-versions?key=' + encodeURIComponent(key))
            .then(res => res.json())
            .then(data => {
                const content = document.getElementById('versionModalContent');
                if (data.versions && data.versions.length) {
                    let html = `<h3>Versions for ${displayName || key}</h3><ul>`;
                    data.versions.forEach(v => {
                        html += `<li>${v.IsLatest ? '<b>Latest</b> ' : ''}VersionId: <code>${v.VersionId}</code> | Size: ${v.Size} | Modified: ${v.LastModified} <button onclick="window.open('/api/download-version?key=${encodeURIComponent(key)}&version_id=${encodeURIComponent(v.VersionId)}','_blank')">Download</button> <button onclick="restoreVersion('${key}','${v.VersionId}')">Restore</button></li>`;
                    });
                    html += '</ul>';
                    html += '<button id="closeVersionModal">Close</button>';
                    content.innerHTML = html;
                } else {
                    content.innerHTML = `<h3>Versions for ${displayName || key}</h3><p>No versions found.</p><button id="closeVersionModal">Close</button>`;
                }
                versionModal.style.display = '';
                document.getElementById('closeVersionModal').onclick = function() {
                    versionModal.style.display = 'none';
                };
            });
    }
    // Restore version
    window.restoreVersion = function(key, versionId) {
        if (!confirm('Restore this version? This will overwrite the current file.')) return;
        fetch('/api/download-version?key=' + encodeURIComponent(key) + '&version_id=' + encodeURIComponent(versionId))
            .then(res => res.blob())
            .then(blob => {
                // Re-upload as latest
                const formData = new FormData();
                formData.append('file', new File([blob], key.split('/').pop()));
                fetch('/api/upload', {
                    method: 'POST',
                    body: formData
                })
                .then(res => res.json())
                .then(data => {
                    if (data.success) {
                        alert('Version restored!');
                        loadFiles();
                        document.getElementById('versionModal').style.display = 'none';
                    } else {
                        alert('Error: ' + data.error);
                    }
                });
            });
    };

    // Create Folder logic
    const createFolderBtn = document.getElementById('createFolderBtn');
    const newFolderInput = document.getElementById('newFolderInput');
    const createFolderResult = document.getElementById('createFolderResult');
    createFolderBtn.onclick = function() {
        const folder = newFolderInput.value.trim();
        if (!folder) {
            createFolderResult.textContent = 'Please enter a folder name.';
            createFolderResult.className = 'alert alert-error';
            createFolderResult.style.display = '';
            setTimeout(() => { createFolderResult.style.display = 'none'; }, 2500);
            return;
        }
        fetch('/api/create-folder', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ folder })
        })
        .then(res => res.json())
        .then(data => {
            createFolderResult.style.display = '';
            if (data.success) {
                createFolderResult.textContent = 'Folder created: ' + data.folder;
                createFolderResult.className = 'alert';
                loadFolders();
                newFolderInput.value = '';
            } else {
                createFolderResult.textContent = data.error || 'Error creating folder.';
                createFolderResult.className = 'alert alert-error';
            }
            setTimeout(() => { createFolderResult.style.display = 'none'; }, 2500);
        });
    };
}); 