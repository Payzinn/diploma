const fileInput = document.getElementById('fileInput');
const filePreview = document.getElementById('filePreview');
const errorMessage = document.getElementById('errorMessage'); 
let filesArray = [];

const dropZone = document.getElementById('dropZone');
dropZone.addEventListener('click', () => {
  fileInput.click();
});

// Настройки валидации
const allowedTypes = [
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'image/jpeg'
];

const allowedExtensions = ['doc', 'docx', 'jpg', 'jpeg'];

// Обработчик изменения файлов
fileInput.addEventListener('change', () => {
    errorMessage.textContent = '';
    const newFiles = Array.from(fileInput.files);
    
    // Фильтрация файлов
    const validFiles = newFiles.filter(file => {
        const extension = file.name.split('.').pop().toLowerCase();
        return allowedTypes.includes(file.type) || 
               allowedExtensions.includes(extension);
    });

    // Обработка ошибок
    if (validFiles.length < newFiles.length) {
        errorMessage.textContent = 'Можно загружать только Word (.doc, .docx) и изображения (.jpg, .jpeg)';
        errorMessage.style.color = 'red';
    }

    // Обновление массива файлов
    filesArray = [...filesArray, ...validFiles];
    updatePreview();
});

// Обновление превью 
function updatePreview() {
    filePreview.innerHTML = '';
    
    filesArray.forEach((file, index) => {
        const fileItem = document.createElement('div');
        fileItem.className = 'file-item';
        
        const fileInfo = document.createElement('span');
        fileInfo.textContent = `${file.name} (${(file.size/1024).toFixed(2)} KB)`;
        
        const removeBtn = document.createElement('span');
        removeBtn.className = 'remove-btn';
        removeBtn.textContent = '×';
        removeBtn.onclick = () => removeFile(index);
        
        fileItem.appendChild(fileInfo);
        fileItem.appendChild(removeBtn);
        filePreview.appendChild(fileItem);
    });

    // Обновляем FileList в input
    const dataTransfer = new DataTransfer();
    filesArray.forEach(file => dataTransfer.items.add(file));
    fileInput.files = dataTransfer.files;
}

// Удаление файла 
function removeFile(index) {
    filesArray = filesArray.filter((_, i) => i !== index);
    updatePreview();
}