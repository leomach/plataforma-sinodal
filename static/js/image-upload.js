let cropper;
const cropModal = document.getElementById('crop-modal');
const cropImage = document.getElementById('crop-image');
const cropConfirm = document.getElementById('crop-confirm');

function openCropModal(imageSrc) {
    cropImage.src = imageSrc;
    cropModal.classList.remove('hidden');
    document.body.style.overflow = 'hidden';
}

function closeCropModal() {
    cropModal.classList.add('hidden');
    document.body.style.overflow = '';
    if (cropper) {
        cropper.destroy();
        cropper = null;
    }
}

function initCropper(aspectRatio) {
    if (cropper) cropper.destroy();
    cropper = new Cropper(cropImage, {
        aspectRatio: aspectRatio,
        viewMode: 1,
        guides: true,
        autoCropArea: 1,
        responsive: true,
        restore: false,
    });
}

/**
 * Configura o upload de imagem com corte e compressão.
 * @param {string} inputId - ID do input file
 * @param {string} previewId - ID do elemento de preview (img ou div)
 * @param {number} aspectRatio - Proporção do corte (ex: 1 para avatar, 16/9 para banner)
 * @param {boolean} autoSubmit - Se true, submete o formulário automaticamente após confirmar o corte
 */
function setupImageUpload(inputId, previewId, aspectRatio = 1, autoSubmit = false) {
    const input = document.getElementById(inputId);
    const preview = document.getElementById(previewId);
    
    if (!input) {
        console.warn(`Input com ID "${inputId}" não encontrado.`);
        return;
    }

    input.addEventListener('change', (e) => {
        const files = e.target.files;
        if (files && files.length > 0) {
            const reader = new FileReader();
            reader.onload = () => {
                openCropModal(reader.result);
                // Pequeno delay para garantir que a imagem carregou no modal
                setTimeout(() => initCropper(aspectRatio), 100);
                
                cropConfirm.onclick = () => {
                    if (!cropper) return;
                    
                    // Adicionar feedback visual de processamento
                    cropConfirm.disabled = true;
                    cropConfirm.innerText = 'Processando...';

                    const canvas = cropper.getCroppedCanvas();
                    canvas.toBlob((blob) => {
                        new Compressor(blob, {
                            quality: 0.6,
                            maxWidth: aspectRatio > 1 ? 1200 : 500,
                            success(result) {
                                console.log('Imagem processada com sucesso:', result.size / 1024, 'KB');
                                
                                // Criar um novo arquivo a partir do blob comprimido
                                const croppedFile = new File([result], files[0].name, {
                                    type: 'image/jpeg',
                                    lastModified: Date.now(),
                                });
                                
                                // Substituir o arquivo no input original usando DataTransfer
                                const dataTransfer = new DataTransfer();
                                dataTransfer.items.add(croppedFile);
                                input.files = dataTransfer.files;
                                
                                // Atualizar o preview visual
                                if (preview) {
                                    const previewUrl = URL.createObjectURL(result);
                                    if (preview.tagName === 'IMG') {
                                        preview.src = previewUrl;
                                    } else {
                                        preview.style.backgroundImage = `url(${previewUrl})`;
                                        preview.style.backgroundSize = 'cover';
                                        preview.style.backgroundPosition = 'center';
                                        preview.innerHTML = '';
                                    }
                                }
                                
                                // Resetar botão e fechar modal
                                cropConfirm.disabled = false;
                                cropConfirm.innerText = 'Confirmar e Cortar';
                                closeCropModal();

                                if (autoSubmit) {
                                    const form = input.closest('form');
                                    if (form) {
                                        form.requestSubmit ? form.requestSubmit() : form.submit();
                                    }
                                }

                                console.log('Input atualizado com arquivo processado. Pronto para envio.');
                            },
                            error(err) {
                                console.error('Erro na compressão:', err.message);
                                cropConfirm.disabled = false;
                                cropConfirm.innerText = 'Confirmar e Cortar';
                                closeCropModal();
                            },
                        });
                    }, 'image/jpeg');
                };
            };
            reader.readAsDataURL(files[0]);
        }
    });
}
