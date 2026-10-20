async function loadAdminWorks(){
  const grid = document.getElementById('adminGrid');
  try{
    const res = await fetch('/api/portfolios');
    const data = await res.json();
    grid.innerHTML = '';
    data.forEach(item=>{
      const div = document.createElement('div');
      div.className = 'admin-card';
      div.innerHTML = `
        <img src="${item.image_url}" alt="${item.title}" loading="lazy">
        <div class="card-info">
          <h4>${item.title}</h4>
          <span style="font-size:12px;color:var(--muted);background:#1e1e32;padding:3px 8px;border-radius:10px">${item.category}</span>
          <div class="actions">
            <button class="delete" onclick="deleteItem('${item.id}')">Delete</button>
          </div>
        </div>
      `;
      grid.appendChild(div);
    });
    if(data.length===0) grid.innerHTML = '<p style="color:var(--muted)">No works yet. Upload your first project.</p>';
  }catch(e){ grid.innerHTML = '<p>Failed to load works</p>'; }
}

async function deleteItem(id){
  if(!confirm('Delete this work?')) return;
  try{
    const res = await fetch(`/api/delete/${id}`, {method:'DELETE'});
    const d = await res.json();
    if(d.success) loadAdminWorks(); else alert('Failed: '+d.error);
  }catch(e){ alert('Error deleting'); }
}

document.getElementById('uploadForm')?.addEventListener('submit', async (e)=>{
  e.preventDefault();
  const btn = document.getElementById('uploadBtn');
  const status = document.getElementById('uploadStatus');
  const formData = new FormData(e.target);
  btn.textContent = 'Uploading...'; btn.disabled = true;
  status.textContent = '';
  try{
    const res = await fetch('/api/upload', {method:'POST', body:formData});
    const data = await res.json();
    if(data.success){
      status.style.color = '#38e6ff'; status.textContent = 'Uploaded!';
      e.target.reset(); loadAdminWorks();
    }else{
      status.style.color = '#ff4e4e'; status.textContent = 'Error: '+data.error;
    }
  }catch(err){
    status.style.color = '#ff4e4e'; status.textContent = 'Upload failed';
  }finally{ btn.textContent = 'Upload'; btn.disabled = false; }
});

document.addEventListener('DOMContentLoaded', loadAdminWorks);