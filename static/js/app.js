document.addEventListener('DOMContentLoaded', function () {
  // Inicialización de tooltips si existen
  var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
  tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
  });

  // Auto-cierre de alertas flash a los 6 segundos
  const alerts = document.querySelectorAll('.alert-dismissible');
  alerts.forEach(function (alert) {
    setTimeout(function () {
      try {
        const bsAlert = new bootstrap.Alert(alert);
        bsAlert.close();
      } catch (e) {}
    }, 6000);
  });
});
