document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('simForm');
    const loader = document.getElementById('loader');
    
    // 1. LOADING SCREEN HANDLING
    // Menampilkan loader saat form disubmit untuk memberikan feedback ke user
    if(form) {
        form.addEventListener('submit', function(e) {
            const city = document.getElementById('city').value;
            // Validasi sederhana: Cek apakah kota sudah dipilih
            if(!city) {
                e.preventDefault();
                alert("Silakan pilih Wilayah Perkebunan terlebih dahulu.");
                return;
            }
            // Munculkan loader
            loader.classList.remove('hidden');
        });
    }

    // 2. MODAL POP-UP LOGIC
    // Fungsi untuk membuka modal (Cara Baca)
    window.openModal = function() {
        const modal = document.getElementById('infoModal');
        if(modal) {
            modal.classList.remove('hidden');
        }
    };

    // Fungsi untuk menutup modal
    window.closeModal = function() {
        const modal = document.getElementById('infoModal');
        if(modal) {
            modal.classList.add('hidden');
        }
    };

    // Tutup modal jika user klik area gelap (overlay) di luar kartu
    const modalOverlay = document.getElementById('infoModal');
    if(modalOverlay) {
        modalOverlay.addEventListener('click', (e) => {
            if(e.target === modalOverlay) {
                closeModal();
            }
        });
    }
    
    // Tutup modal jika user menekan tombol ESC di keyboard
    document.addEventListener('keydown', (e) => {
        if(e.key === "Escape") {
            closeModal();
        }
    });
});