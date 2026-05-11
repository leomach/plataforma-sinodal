// Main JavaScript
console.log('Plataforma Sinodal carregada');

// Máscara para Telefone/WhatsApp
document.addEventListener('DOMContentLoaded', () => {
    const phoneInputs = document.querySelectorAll('.phone-mask');

    const applyMask = (input) => {
        let v = input.value.replace(/\D/g, "");
        if (v.length > 11) v = v.slice(0, 11);
        v = v.replace(/^(\d{2})(\d)/g, "($1) $2");
        v = v.replace(/(\d)(\d{4})$/, "$1-$2");
        input.value = v;
    };

    phoneInputs.forEach(input => {
        // Aplica a máscara inicialmente caso já tenha valor
        applyMask(input);

        input.addEventListener('input', (e) => {
            applyMask(e.target);
        });
    });
});

