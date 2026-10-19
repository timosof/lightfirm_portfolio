document.addEventListener('DOMContentLoaded', ()=>{
  loadAdminGrid();

  const form = document.getElementById('uploadForm');
  form.addEventListener('submit', async (e)=>{
    e.preventDefault();
    const btn = document.getElementById('uploadBtn');
    const status = document.getElementById('uploadStatus');
    btn.textContent = 'Uploading...';
    btn.disabled = true;

    const formData = new FormData();
    formData.append('title', document.getElementById('title').value);
    formData.append('category', document.getElementById('category').value);
    formData.append('image', document.getElementById('image').files[0]);

    try{
      const res = await fetch('/api/upload', {method:'POST', body:formData});
      const data = await res.json();
      if(data.success){
        status.textContent = 'Uploaded successfully!';
        form.reset();
        loadAdminGrid();
      }else{
        status.textContent = 'Error: ' + data.error;
      }
    }catch(err){
      status.textContent = 'Upload failed.';
    }
    btn.textContent = 'Upload';
    btn.disabled = false;
  });
});

async function loadAdminGrid(){
  const grid = document.getElementById('adminGrid');
  const res = await fetch('/api/portfolios');
  const data = await res.json();
  grid.innerHTML = '';
  data.forEach(item=>{
    const div = document.createElement('div');
    div.className = 'admin-card';
    div.innerHTML = `<img src="${item.image_url}"><div style="padding:10px"><b>${item.title}</b><br><small>${item.category}</small></div><button onclick="deleteItem('${item.id}')">Delete</button>`;
    grid.appendChild(div);
  });
}

async function deleteItem(id){
  if(!confirm('Delete this work?')) return;
  await fetch('/api/delete/'+id, {method:'DELETE'});
  loadAdminGrid();
}