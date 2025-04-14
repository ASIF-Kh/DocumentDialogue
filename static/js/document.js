document.addEventListener("DOMContentLoaded", function () {
  // Function to confirm document deletion
  window.confirmDelete = function (documentId, documentName) {
    const deleteModal = new bootstrap.Modal(
      document.getElementById("deleteModal")
    );
    const documentNameElement = document.getElementById("documentName");
    const deleteForm = document.getElementById("deleteForm");

    // Set document name in modal
    documentNameElement.textContent = documentName;

    // Set form action
    deleteForm.action = `/delete/${documentId}`;

    // Show modal
    deleteModal.show();
  };

  // Function to confirm group chat deletion
  window.confirmDeleteGroupChat = function (groupChatId, chatName) {
    const deleteModal = new bootstrap.Modal(
      document.getElementById("deleteGroupChatModal")
    );
    const chatNameElement = document.getElementById("groupChatName");
    const deleteForm = document.getElementById("deleteGroupChatForm");

    // Set chat name in modal
    chatNameElement.textContent = chatName;

    // Set form action
    deleteForm.action = `/delete_group_chat/${groupChatId}`;

    // Show modal
    deleteModal.show();
  };

  // File upload validation
  const uploadForm = document.querySelector('form[action*="upload"]');
  const fileInput = document.querySelector('input[type="file"]');

  if (uploadForm && fileInput) {
    fileInput.addEventListener("change", function () {
      const file = this.files[0];
      if (file) {
        // Check file type
        const fileType = file.name.split(".").pop().toLowerCase();
        const allowedTypes = ["pdf", "txt", "docx"];

        if (!allowedTypes.includes(fileType)) {
          alert(`Invalid file type. Allowed types: ${allowedTypes.join(", ")}`);
          this.value = "";
          return;
        }

        // Check file size (max 16MB)
        const maxSize = 16 * 1024 * 1024;
        if (file.size > maxSize) {
          alert("File is too large. Maximum size is 16MB.");
          this.value = "";
          return;
        }
      }
    });

    uploadForm.addEventListener("submit", function (e) {
      if (fileInput.files.length === 0) {
        e.preventDefault();
        alert("Please select a file to upload.");
      }
    });
  }

  // Add loading spinner on form submission
  const allForms = document.querySelectorAll("form");
  allForms.forEach((form) => {
    form.addEventListener("submit", function () {
      const submitButton = this.querySelector('button[type="submit"]');
      if (submitButton) {
        const originalText = submitButton.innerHTML;
        submitButton.innerHTML =
          '<i class="fas fa-spinner fa-spin me-2"></i>Processing...';
        submitButton.disabled = true;

        // Re-enable after timeout (in case of errors)
        setTimeout(() => {
          submitButton.innerHTML = originalText;
          submitButton.disabled = false;
        }, 30000);
      }
    });
  });
});
