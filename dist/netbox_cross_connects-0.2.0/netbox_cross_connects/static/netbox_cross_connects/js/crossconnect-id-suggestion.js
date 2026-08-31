(() => {
  const siteField = document.getElementById('id_site');
  const crossConnectIdField = document.getElementById('id_cross_connect_id');
  const endpoint = siteField?.dataset.crossConnectIdUrl;

  if (!siteField || !crossConnectIdField || !endpoint) {
    return;
  }

  const feedback = document.createElement('div');
  feedback.className = 'form-text text-warning d-none';
  crossConnectIdField.insertAdjacentElement('afterend', feedback);

  let requestCounter = 0;

  const clearFeedback = () => {
    feedback.textContent = '';
    feedback.classList.add('d-none');
  };

  const showFeedback = (message) => {
    feedback.textContent = message;
    feedback.classList.remove('d-none');
  };

  siteField.addEventListener('change', async () => {
    if (crossConnectIdField.value.trim()) {
      return;
    }

    clearFeedback();
    if (!siteField.value) {
      return;
    }

    const requestId = ++requestCounter;
    try {
      const response = await fetch(`${endpoint}?${new URLSearchParams({site_id: siteField.value})}`, {
        headers: {'X-Requested-With': 'XMLHttpRequest'},
      });
      const data = await response.json();

      if (requestId !== requestCounter || crossConnectIdField.value.trim()) {
        return;
      }

      if (!response.ok) {
        showFeedback(data.error || gettext('Unable to suggest a Cross Connect ID.'));
        return;
      }

      crossConnectIdField.value = data.cross_connect_id;
    } catch (_error) {
      if (requestId === requestCounter && !crossConnectIdField.value.trim()) {
        showFeedback(gettext('Unable to suggest a Cross Connect ID.'));
      }
    }
  });
})();
