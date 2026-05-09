# PRD - Gestão de Imagens e Persistência (Cloudinary)

## 1. Visão Geral
Para garantir que as imagens (fotos de perfil, banners de eventos, etc.) não sejam perdidas nos deploys da Railway e para oferecer uma experiência de usuário moderna, a plataforma utilizará o **Cloudinary** como storage oficial e ferramentas de tratamento de imagem no front-end.

## 2. Casos de Uso
- **Foto de Perfil:** O usuário deve poder subir e cortar sua foto em formato circular/quadrado.
- **Banner de Evento:** O organizador deve poder subir imagens grandes e ajustar o enquadramento para o formato de cabeçalho.
- **Documentos/Anexos (Futuro):** Armazenamento seguro de comprovantes se necessário.

---

## 3. Arquitetura Técnica

### 3.1. Storage Backend (Persistência)
- **Provedor:** [Cloudinary](https://cloudinary.com/) (Plano Free).
- **Integração Django:** `django-cloudinary-storage` + `cloudinary`.
- **Benefício:** CDN automática, redimensionamento dinâmico via URL e persistência independente do servidor da aplicação.

### 3.2. Processamento Client-Side (Performance)
Para evitar o upload de arquivos desnecessariamente pesados e garantir o enquadramento correto:
- **Compressão:** `browser-image-compression` ou `Compressor.js` para reduzir o tamanho do arquivo antes do envio (meta: < 500KB).
- **Corte (Cropping):** `Cropper.js` para permitir que o usuário selecione a melhor área da imagem.

---

## 4. Requisitos de Interface (UX/UI)

### 4.1. Fluxo de Upload (Modal)
O upload não deve ser um simples "input file" seco. O fluxo seguirá:
1. **Trigger:** Clique no avatar ou no placeholder do banner.
2. **Modal de Seleção:** Área de "Arrastar e Soltar" (Drag & Drop) com preview imediato.
3. **Ajuste:** Interface de corte (Crop) ativa automaticamente após a seleção da imagem.
4. **Feedback:** Barra de progresso durante o upload para a Cloudinary.

### 4.2. Especificações de Formato
- **Avatar:** Aspect Ratio 1:1 (Quadrado), mínimo 200x200px.
- **Banner:** Aspect Ratio 16:9 ou 21:9, mínimo 1200x400px.

---

## 5. Bibliotecas Recomendadas

1.  **Back-end:**
    - `cloudinary`: SDK oficial.
    - `django-cloudinary-storage`: Facilita a integração com `ImageField`.
2.  **Front-end:**
    - `Cropper.js`: Líder de mercado para manipulação visual de imagens.
    - `Dropzone.js` ou `FilePond`: Para uma área de upload rica e intuitiva.

---

## 6. Segurança e Otimização
- **Lazy Loading:** Imagens de banners devem carregar com lazy loading nativo do navegador.
- **WebP:** Configurar a Cloudinary para entregar imagens no formato WebP automaticamente para navegadores compatíveis (reduz consumo de dados).
- **Validação:** Limite de 5MB no front-end para evitar travamentos durante o processo de compressão.

---

## 7. Próximos Passos
1. Criar conta na Cloudinary e obter as API Keys.
2. Configurar variáveis de ambiente (`CLOUDINARY_URL`) na Railway.
3. Implementar o widget de upload com suporte a corte.
