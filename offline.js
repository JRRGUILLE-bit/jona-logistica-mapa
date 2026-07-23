(() => {
  const isGitHubPages = location.hostname.endsWith('.github.io');
  const basePath = isGitHubPages ? '/jona-logistica/' : '/';
  const workerUrl = `${basePath}service-worker.js`;
  const canonicalUrl = new URL(basePath, location.origin).href;
  const isStandalone = window.matchMedia('(display-mode: standalone)').matches || navigator.standalone === true;
  const isIOS = /iphone|ipad|ipod/i.test(navigator.userAgent);
  let deferredInstallPrompt = null;
  let statusTimer = null;

  const style = document.createElement('style');
  style.textContent = `
    .skip-link{
      position:fixed;left:max(12px,env(safe-area-inset-left));top:max(10px,env(safe-area-inset-top));
      z-index:10001;padding:10px 14px;border:1px solid rgba(240,170,86,.75);
      border-radius:12px;background:#07151d;color:#f5f0e8;
      font:700 11px/1.2 Inter,system-ui,sans-serif;letter-spacing:.04em;text-decoration:none;
      transform:translateY(-160%);transition:transform .18s ease;
    }
    .skip-link:focus{transform:translateY(0);outline:3px solid #ffd18f;outline-offset:3px}
    .site-tools{
      margin:22px 0 0;padding:15px 16px;display:flex;align-items:center;justify-content:center;
      gap:9px;flex-wrap:wrap;border:1px solid rgba(255,255,255,.10);border-radius:14px;
      background:linear-gradient(145deg,rgba(4,20,32,.72),rgba(7,31,46,.58));
      box-shadow:inset 0 1px rgba(255,255,255,.035);
    }
    .site-tool-button{
      min-height:44px;padding:10px 15px;display:inline-flex;align-items:center;justify-content:center;
      gap:8px;border:1px solid rgba(220,145,64,.48);border-radius:999px;
      background:rgba(4,20,32,.74);color:#f5f0e8;cursor:pointer;
      font:700 10px/1.2 Inter,system-ui,sans-serif;letter-spacing:.075em;text-transform:uppercase;
      transition:transform .18s ease,border-color .18s ease,background .18s ease;
      touch-action:manipulation;-webkit-tap-highlight-color:rgba(220,145,64,.18);
    }
    .site-tool-button:hover{transform:translateY(-2px);border-color:#f0aa56;background:rgba(9,38,55,.94)}
    .site-tool-button:focus-visible{outline:3px solid #ffd18f;outline-offset:3px}
    .site-tool-button svg{width:16px;height:16px;fill:none;stroke:currentColor;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}
    .site-tool-note{color:rgba(245,240,232,.58);font:600 10px/1.45 Inter,system-ui,sans-serif;letter-spacing:.035em}
    .offline-status{
      position:fixed;right:max(12px,env(safe-area-inset-right));bottom:max(12px,env(safe-area-inset-bottom));
      z-index:9999;max-width:min(430px,calc(100vw - 24px));padding:10px 12px;
      display:flex;align-items:center;justify-content:center;gap:10px;
      border:1px solid rgba(240,170,86,.62);border-radius:14px;
      background:rgba(4,20,32,.97);color:#f5f0e8;
      box-shadow:0 14px 34px rgba(0,0,0,.40);
      font:600 11px/1.35 Inter,system-ui,sans-serif;letter-spacing:.025em;text-align:left;
      transform:translateY(150%);opacity:0;pointer-events:none;
      transition:transform .2s ease,opacity .2s ease;
    }
    .offline-status[data-tone="success"]{border-color:rgba(110,194,154,.72)}
    .offline-status.is-visible{transform:translateY(0);opacity:1;pointer-events:auto}
    .offline-status button{
      flex:0 0 auto;min-height:34px;padding:7px 10px;border:1px solid rgba(240,170,86,.58);
      border-radius:999px;background:rgba(220,145,64,.13);color:#f5f0e8;cursor:pointer;
      font:700 9px/1 Inter,system-ui,sans-serif;letter-spacing:.06em;text-transform:uppercase;
    }
    .offline-status button:focus-visible{outline:3px solid #ffd18f;outline-offset:2px}
    [hidden]{display:none!important}
    :where(a,button,[role="button"]){touch-action:manipulation}
    :where(h1,h2,h3){text-wrap:balance}
    :where(p,.action-description,.next-shoot-copy span){text-wrap:pretty}
    @media(max-width:620px){
      .site-tools{display:grid;grid-template-columns:1fr 1fr;padding:12px}
      .site-tool-button{width:100%}
      .site-tool-note{grid-column:1/-1;text-align:center}
      .offline-status{left:max(12px,env(safe-area-inset-left));right:max(12px,env(safe-area-inset-right))}
    }
    @media(hover:none){
      .site-tool-button:hover{transform:none}
    }
    @media(prefers-reduced-motion:reduce){
      .skip-link,.site-tool-button,.offline-status{transition:none}
    }
  `;
  document.head.appendChild(style);


  const mainContent = document.querySelector('main');
  if (mainContent) {
    if (!mainContent.id) mainContent.id = 'main-content';
    if (!document.querySelector('.skip-link')) {
      const skipLink = document.createElement('a');
      skipLink.className = 'skip-link';
      skipLink.href = `#${mainContent.id}`;
      skipLink.textContent = 'Saltar al contenido';
      document.body.prepend(skipLink);
    }
  }

  const status = document.createElement('div');
  status.className = 'offline-status';
  status.setAttribute('role', 'status');
  status.setAttribute('aria-live', 'polite');
  status.setAttribute('aria-atomic', 'true');
  document.body.appendChild(status);

  const hideStatus = () => {
    clearTimeout(statusTimer);
    status.classList.remove('is-visible');
    status.replaceChildren();
    if (!navigator.onLine) {
      window.setTimeout(() => showStatus(
        'Sin conexión · mostrando la última versión guardada. El clima puede estar desactualizado.',
        { persistent: true }
      ), 0);
    }
  };

  function showStatus(message, { persistent = false, tone = 'info', actionLabel = '', action = null } = {}) {
    clearTimeout(statusTimer);
    status.dataset.tone = tone;
    const text = document.createElement('span');
    text.textContent = message;
    status.replaceChildren(text);

    if (actionLabel && typeof action === 'function') {
      const button = document.createElement('button');
      button.type = 'button';
      button.textContent = actionLabel;
      button.addEventListener('click', action, { once: true });
      status.appendChild(button);
    }

    status.classList.add('is-visible');
    if (!persistent) statusTimer = window.setTimeout(hideStatus, 4300);
  }

  if (!navigator.onLine) {
    showStatus(
      'Sin conexión · mostrando la última versión guardada. El clima puede estar desactualizado.',
      { persistent: true }
    );
  }

  window.addEventListener('offline', () => {
    showStatus(
      'Sin conexión · mostrando la última versión guardada. El clima puede estar desactualizado.',
      { persistent: true }
    );
  });

  window.addEventListener('online', () => {
    showStatus('Conexión recuperada · ya podés actualizar la información.', { tone: 'success' });
  });

  if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
      navigator.serviceWorker.register(workerUrl, {
        scope: basePath,
        updateViaCache: 'none'
      }).then(registration => {
        registration.update().catch(() => {});
      }).catch(error => {
        console.warn('No se pudo activar el modo offline.', error);
      });
    });
  }

  const footer = document.querySelector('.footer');
  const actions = document.querySelector('.actions');
  if (!footer || !actions) return;

  const tools = document.createElement('section');
  tools.className = 'site-tools';
  tools.setAttribute('aria-label', 'Acciones rápidas del sitio');
  tools.innerHTML = `
    <button class="site-tool-button" id="shareSite" type="button">
      <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="18" cy="5" r="3"></circle><circle cx="6" cy="12" r="3"></circle><circle cx="18" cy="19" r="3"></circle><path d="M8.6 10.6l6.8-4.2M8.6 13.4l6.8 4.2"></path></svg>
      Compartir
    </button>
    <button class="site-tool-button" id="installSite" type="button" hidden>
      <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3v12M7 10l5 5 5-5"></path><path d="M5 20h14"></path></svg>
      Instalar app
    </button>
    <span class="site-tool-note">Se puede usar sin conexión después de abrirla una vez online.</span>
  `;
  footer.before(tools);

  const shareButton = tools.querySelector('#shareSite');
  const installButton = tools.querySelector('#installSite');

  const copyText = async text => {
    try {
      await navigator.clipboard.writeText(text);
      return true;
    } catch {
      try {
        const field = document.createElement('textarea');
        field.value = text;
        field.setAttribute('readonly', '');
        field.style.position = 'fixed';
        field.style.opacity = '0';
        document.body.appendChild(field);
        field.select();
        const copied = document.execCommand('copy');
        field.remove();
        return copied;
      } catch {
        return false;
      }
    }
  };

  shareButton.addEventListener('click', async () => {
    const shareData = {
      title: 'Jona tenía 15 años — Base de operaciones',
      text: 'Clima, movilidad, documentos y herramientas del rodaje.',
      url: canonicalUrl
    };

    try {
      if (navigator.share) {
        await navigator.share(shareData);
        return;
      }
      if (await copyText(canonicalUrl)) {
        showStatus('Enlace copiado al portapapeles.', { tone: 'success' });
      } else {
        showStatus('No se pudo copiar el enlace.');
      }
    } catch (error) {
      if (error?.name === 'AbortError') return;
      if (await copyText(canonicalUrl)) {
        showStatus('Enlace copiado al portapapeles.', { tone: 'success' });
      } else {
        showStatus('No se pudo compartir el sitio.');
      }
    }
  });

  if (!isStandalone && isIOS) {
    installButton.hidden = false;
    installButton.textContent = 'Agregar al inicio';
  }

  window.addEventListener('beforeinstallprompt', event => {
    event.preventDefault();
    deferredInstallPrompt = event;
    if (!isStandalone) installButton.hidden = false;
  });

  installButton.addEventListener('click', async () => {
    if (deferredInstallPrompt) {
      deferredInstallPrompt.prompt();
      const choice = await deferredInstallPrompt.userChoice;
      deferredInstallPrompt = null;
      installButton.hidden = true;
      if (choice.outcome === 'accepted') {
        showStatus('Base instalada en el dispositivo.', { tone: 'success' });
      }
      return;
    }

    if (isIOS) {
      showStatus('En Safari: tocá Compartir y después “Agregar a pantalla de inicio”.', { persistent: false });
    }
  });

  window.addEventListener('appinstalled', () => {
    deferredInstallPrompt = null;
    installButton.hidden = true;
    showStatus('Base instalada en el dispositivo.', { tone: 'success' });
  });
})();
