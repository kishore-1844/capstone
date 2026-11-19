document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('task-form');
  const open = document.getElementById('open-task-form');
  const close = document.getElementById('close-task-form');
  if (!form || !open) return;
  open.addEventListener('click', () => {
    form.classList.remove('hidden');
    form.querySelector('input[name="title"]').focus();
    form.scrollIntoView({ behavior: 'smooth', block: 'center' });
  });
  close.addEventListener('click', () => form.classList.add('hidden'));

  let draggedTask = null;
  document.querySelectorAll('.task-card[draggable="true"]').forEach(card => {
    card.addEventListener('dragstart', event => {
      if (event.target.closest('button, input, select, textarea, summary, form')) {
        event.preventDefault();
        return;
      }
      draggedTask = card;
      event.dataTransfer.effectAllowed = 'move';
      event.dataTransfer.setData('text/plain', card.dataset.taskId);
    });
    card.addEventListener('dragend', () => {
      draggedTask = null;
      document.querySelectorAll('.kanban-column').forEach(column => column.classList.remove('drag-over'));
    });
  });
  document.querySelectorAll('.kanban-column').forEach(column => {
    column.addEventListener('dragover', event => {
      if (!draggedTask) return;
      event.preventDefault();
      column.classList.add('drag-over');
    });
    column.addEventListener('dragleave', event => {
      if (!column.contains(event.relatedTarget)) column.classList.remove('drag-over');
    });
    column.addEventListener('drop', async event => {
      if (!draggedTask) return;
      event.preventDefault();
      column.classList.remove('drag-over');
      const taskId = event.dataTransfer.getData('text/plain');
      const formData = new URLSearchParams({ status: column.dataset.status });
      const response = await fetch(`/tasks/${taskId}/update`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: formData
      });
      if (response.ok) window.location.reload();
    });
  });
});
