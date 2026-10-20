// Mobile hamburger
document.addEventListener('DOMContentLoaded', () => {
  const hamburger = document.getElementById('hamburger');
  const navLinks = document.getElementById('navLinks');
  if(hamburger){
    hamburger.addEventListener('click', ()=>{
      navLinks.classList.toggle('active');
      hamburger.textContent = navLinks.classList.contains('active') ? '✕' : '☰';
    });
  }
});

// Portfolio page load
document.addEventListener('DOMContentLoaded', () => {
  const portfolioGrid = document.getElementById('portfolioGrid');
  if(portfolioGrid){
    loadPortfolio(portfolioGrid);
  }

  // Contact form
  const contactForm = document.getElementById('contactForm');
  if(contactForm){
    contactForm.addEventListener('submit', async (e)=>{
      e.preventDefault();
      const status = document.getElementById('contactStatus');
      status.textContent = 'Sending...';
      try{
        const res = await fetch('/api/contact',{
          method:'POST',
          headers:{'Content-Type':'application/json'},
          body: JSON.stringify({
            name: document.getElementById('c_name').value,
            email: document.getElementById('c_email').value,
            message: document.getElementById('c_message').value
          })
        });
        const data = await res.json();
        if(data.success){
          status.textContent = 'Message sent! We will reply soon.';
          contactForm.reset();
        }else{
          status.textContent = 'Error: ' + data.error;
        }
      }catch(err){
        status.textContent = 'Failed to send.';
      }
    });
  }
});

async function loadPortfolio(grid){
  try{
    const res = await fetch('/api/portfolios');
    const data = await res.json();
    grid.innerHTML = '';
    let allItems = data;

    const render = (items)=>{
      grid.innerHTML = '';
      items.forEach(item=>{
        const div = document.createElement('div');
        div.className = 'card';
        div.dataset.category = item.category;
        div.innerHTML = `<img src="${item.image_url}"><div class="card-info"><h4>${item.title}</h4><span>${item.category}</span></div>`;
        div.addEventListener('click', ()=> openLightbox(item));
        grid.appendChild(div);
      });
    };

    render(allItems);

    // Filters
    document.querySelectorAll('.filter-btn').forEach(btn=>{
      btn.addEventListener('click', ()=>{
        document.querySelectorAll('.filter-btn').forEach(b=>b.classList.remove('active'));
        btn.classList.add('active');
        const filter = btn.dataset.filter;
        if(filter === 'All') render(allItems);
        else render(allItems.filter(i=>i.category === filter));
      });
    });

  }catch(e){
    grid.innerHTML = '<p>No works yet. Admin should upload.</p>';
  }
}

function openLightbox(item){
  const lb = document.getElementById('lightbox');
  if(!lb) return;
  document.getElementById('lightboxImg').src = item.image_url;
  document.getElementById('lightboxCaption').textContent = item.title + ' - ' + item.category;
  lb.style.display = 'flex';
  lb.querySelector('.close').onclick = ()=> lb.style.display='none';
  lb.onclick = (e)=> { if(e.target===lb) lb.style.display='none'; }
}