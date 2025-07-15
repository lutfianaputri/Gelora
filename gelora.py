import psycopg2
import uuid
import datetime
import pytz

DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "Gelora - Pagelaran Karya"
DB_USER = "postgres"
DB_PASSWORD = "lutfiana putri"

conn = None
cur = None

current_user_id = None
current_user_role = None
current_user_name = None

STS_PEMBAYARAN = ('belum_bayar', 'menunggu_pembayaran', 'sudah_bayar', 'gagal')
STS_TIKET = ('aktif', 'digunakan', 'dibatalkan')
JENIS_DISKON_ENUM = ('persentase', 'nominal')
METODE_BAYAR_ENUM = ('transfer_bank', 'qris', 'e_wallet')

def connect_db():
    global conn, cur
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        cur = conn.cursor()
        print("Koneksi database berhasil.")
    except psycopg2.Error as e:
        print(f"Gagal terhubung ke database: {e}")
        conn = None
        cur = None

def close_db():
    global conn, cur
    if cur:
        cur.close()
    if conn:
        conn.close()
    print("Koneksi database ditutup.")

def execute_query(query, params=None, fetch_one=False, fetch_all=False):
    global conn, cur
    if not conn or conn.closed:
        connect_db()

    if not conn:
        print("Tidak ada koneksi database yang aktif.")
        return None

    try:
        cur.execute(query, params)
        if fetch_one:
            return cur.fetchone()
        elif fetch_all:
            return cur.fetchall()
        else:
            conn.commit()
            return True
    except psycopg2.Error as e:
        print(f"Terjadi kesalahan database: {e}")
        conn.rollback()
        return False

def registrasi_user(nama_lengkap, email, password, nomor_telepon, id_role):
    try:
        user_id = uuid.uuid4()
        query = """
        INSERT INTO "user" (id_user, nama_lengkap, email, password, nomor_telepon, id_role)
        VALUES (%s, %s, %s, %s, %s, %s);
        """
        if execute_query(query, (str(user_id), nama_lengkap, email, password, nomor_telepon, id_role)):
            print(f"Registrasi {nama_lengkap} berhasil!")
            return True
        else:
            print("Registrasi gagal. Mungkin email atau nomor telepon sudah terdaftar.")
            return False
    except Exception as e:
        print(f"Terjadi kesalahan saat registrasi: {e}")
        return False

def login_user(email, password, expected_role_id):
    global current_user_id, current_user_role, current_user_name
    query = """
    SELECT u.id_user, u.nama_lengkap, r.nama_role
    FROM "user" u
    JOIN roles r ON u.id_role = r.id_role
    WHERE u.email = %s AND u.password = %s AND u.id_role = %s;
    """
    result = execute_query(query, (email, password, expected_role_id), fetch_one=True)
    if result:
        current_user_id = result[0]
        current_user_name = result[1]
        current_user_role = result[2]
        print(f"Login sebagai {current_user_name} ({current_user_role}) berhasil!")
        return True
    else:
        print("Email atau password salah, atau Anda tidak memiliki peran yang sesuai.")
        return False

def login_penyelenggara():
    print("\n--- Login Penyelenggara ---")
    email = input("Masukkan email: ")
    password = input("Masukkan password: ")
    return login_user(email, password, 1)

def registrasi_penyelenggara():
    print("\n--- Registrasi Penyelenggara ---")
    nama_lengkap = input("Masukkan nama lengkap: ")
    email = input("Masukkan email: ")
    password = input("Masukkan password: ")
    nomor_telepon = input("Masukkan nomor telepon: ")
    if not nomor_telepon:
        nomor_telepon = None
    return registrasi_user(nama_lengkap, email, password, nomor_telepon, 1)

def login_penikmat():
    print("\n--- Login Penikmat ---")
    email = input("Masukkan email: ")
    password = input("Masukkan password: ")
    return login_user(email, password, 2)

def registrasi_penikmat():
    print("\n--- Registrasi Penikmat ---")
    nama_lengkap = input("Masukkan nama lengkap: ")
    email = input("Masukkan email: ")
    password = input("Masukkan password: ")
    nomor_telepon = input("Masukkan nomor telepon: ")
    if not nomor_telepon:
        nomor_telepon = None
    return registrasi_user(nama_lengkap, email, password, nomor_telepon, 2)

def tambah_karya():
    if not current_user_id or current_user_role != 'penyelenggara':
        print("Anda harus login sebagai penyelenggara untuk menambah karya.")
        return

    print("\n--- Tambah Karya Baru ---")
    judul_event = input("Judul Event: ")
    deskripsi_event = input("Deskripsi Event (opsional): ")
    tanggal_mulai_str = input("Tanggal Mulai Event (YYYY-MM-DD HH:MM): ")
    tanggal_selesai_str = input("Tanggal Selesai Event: ")
    lokasi = input("Lokasi Event: ")
    poster_event = input("URL Poster Event: ")

    try:
        tanggal_mulai_event = datetime.datetime.strptime(tanggal_mulai_str, '%Y-%m-%d %H:%M')
        tanggal_mulai_event = pytz.timezone('Asia/Jakarta').localize(tanggal_mulai_event)
        tanggal_selesai_event = None
        if tanggal_selesai_str:
            tanggal_selesai_event = datetime.datetime.strptime(tanggal_selesai_str, '%Y-%m-%d %H:%M')
            tanggal_selesai_event = pytz.timezone('Asia/Jakarta').localize(tanggal_selesai_event)
    except ValueError:
        print("Format tanggal salah. Gunakan YYYY-MM-DD HH:MM.")
        return

    event_id = uuid.uuid4()
    query_event = """
    INSERT INTO event (id_event, judul_event, deskripsi_event, tanggal_mulai_event,
                       tanggal_selesai_event, lokasi, poster_event, user_id_user)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
    """
    if not execute_query(query_event, (str(event_id), judul_event, deskripsi_event,
                                       tanggal_mulai_event, tanggal_selesai_event,
                                       lokasi, poster_event, str(current_user_id))):
        print("Gagal menambahkan event.")
        return

    print("Event berhasil ditambahkan. Sekarang tambahkan tipe tiket.")
    while True:
        nama_tipe = input("Nama Tipe Tiket (atau 'selesai' untuk berhenti): ")
        if nama_tipe.lower() == 'selesai':
            break
        try:
            harga = float(input("Harga Tiket: "))
            kuota = int(input("Kuota Tiket: "))
            if harga <= 0 or kuota <= 0:
                print("Harga dan kuota harus lebih dari nol.")
                continue
        except ValueError:
            print("Harga atau kuota tidak valid.")
            continue

        query_tipe_tiket = """
        INSERT INTO tipe_tiket (nama_tipe, harga, kuota, sisa_kuota, event_id_event)
        VALUES (%s, %s, %s, %s, %s);
        """
        if execute_query(query_tipe_tiket, (nama_tipe, harga, kuota, kuota, str(event_id))):
            print(f"Tipe tiket '{nama_tipe}' berhasil ditambahkan.")
        else:
            print(f"Gagal menambahkan tipe tiket '{nama_tipe}'.")
        
        lanjut = input("Tambah tipe tiket lain? (ya/tidak): ").lower()
        if lanjut != 'ya':
            break
    print("Penambahan karya selesai.")
    menu_penyelenggara()


def lihat_karya(show_all=False):
    print("\n--- Daftar Karya ---")
    query = """
    SELECT e.id_event, e.judul_event, e.tanggal_mulai_event, e.lokasi, u.nama_lengkap
    FROM event e
    JOIN "user" u ON e.user_id_user = u.id_user
    """
    params = ()
    if not show_all and current_user_id and current_user_role == 'penyelenggara':
        query += " WHERE e.user_id_user = %s"
        params = (str(current_user_id),)
    query += " ORDER BY e.tanggal_mulai_event DESC;"

    events = execute_query(query, params, fetch_all=True)

    if not events:
        print("Tidak ada karya yang tersedia.")
        return []

    print(f"{'No.':<5} | {'Judul Event':<30} | {'Tanggal Mulai':<20} | {'Lokasi':<25} | {'Penyelenggara':<20}")
    print("-" * 105)
    for i, event in enumerate(events):
        print(f"{i+1:<5} | {event[1]:<30} | {event[2].strftime('%Y-%m-%d %H:%M'):<20} | {event[3]:<25} | {event[4]:<20}")
    print("-" * 105)
    return events

def edit_karya():
    if not current_user_id or current_user_role != 'penyelenggara':
        print("Anda harus login sebagai penyelenggara untuk mengedit karya.")
        return

    events = lihat_karya()
    if not events:
        print("Tidak ada karya yang bisa diedit.")
        menu_penyelenggara()
        return

    try:
        pilihan = int(input("Pilih nomor karya yang ingin diedit: "))
        if 1 <= pilihan <= len(events):
            selected_event_id = events[pilihan-1][0]
        else:
            print("Pilihan tidak valid.")
            menu_penyelenggara()
            return
    except ValueError:
        print("Input tidak valid. Masukkan nomor.")
        menu_penyelenggara()
        return

    query_event_detail = """
    SELECT judul_event, deskripsi_event, tanggal_mulai_event, tanggal_selesai_event,
           lokasi, poster_event
    FROM event WHERE id_event = %s;
    """
    event_detail = execute_query(query_event_detail, (str(selected_event_id),), fetch_one=True)

    if not event_detail:
        print("Event tidak ditemukan.")
        menu_penyelenggara()
        return

    print("\n--- Edit Karya ---")
    print(f"Mengedit Event: {event_detail[0]}")
    print("Biarkan kosong untuk mempertahankan nilai saat ini.")

    new_judul = input(f"Judul Event ({event_detail[0]}): ") or event_detail[0]
    new_deskripsi = input(f"Deskripsi Event ({event_detail[1]}): ") or event_detail[1]
    
    new_tanggal_mulai_str = input(f"Tanggal Mulai Event ({event_detail[2].strftime('%Y-%m-%d %H:%M')}): ")
    new_tanggal_mulai = event_detail[2]
    if new_tanggal_mulai_str:
        try:
            new_tanggal_mulai = datetime.datetime.strptime(new_tanggal_mulai_str, '%Y-%m-%d %H:%M')
            new_tanggal_mulai = pytz.timezone('Asia/Jakarta').localize(new_tanggal_mulai)
        except ValueError:
            print("Format tanggal mulai salah. Menggunakan tanggal lama.")

    new_tanggal_selesai_str = input(f"Tanggal Selesai Event ({event_detail[3].strftime('%Y-%m-%d %H:%M') if event_detail[3] else 'Kosong'}): ")
    new_tanggal_selesai = event_detail[3]
    if new_tanggal_selesai_str:
        try:
            new_tanggal_selesai = datetime.datetime.strptime(new_tanggal_selesai_str, '%Y-%m-%d %H:%M')
            new_tanggal_selesai = pytz.timezone('Asia/Jakarta').localize(new_tanggal_selesai)
        except ValueError:
            print("Format tanggal selesai salah. Menggunakan tanggal lama.")
    elif new_tanggal_selesai_str == '':
        new_tanggal_selesai = None

    new_lokasi = input(f"Lokasi Event ({event_detail[4]}): ") or event_detail[4]
    new_poster = input(f"URL Poster Event ({event_detail[5] if event_detail[5] else 'Kosong'}): ")
    if not new_poster:
        new_poster = None
    elif new_poster == '':
        new_poster = None
    else:
        new_poster = new_poster


    query_update_event = """
    UPDATE event
    SET judul_event = %s, deskripsi_event = %s, tanggal_mulai_event = %s,
        tanggal_selesai_event = %s, lokasi = %s, poster_event = %s
    WHERE id_event = %s;
    """
    if execute_query(query_update_event, (new_judul, new_deskripsi, new_tanggal_mulai,
                                          new_tanggal_selesai, new_lokasi, new_poster,
                                          str(selected_event_id))):
        print("Event berhasil diperbarui.")
    else:
        print("Gagal memperbarui event.")

    print("\n--- Mengelola Tipe Tiket ---")
    query_tipe_tiket = "SELECT id_tipe_tiket, nama_tipe, harga, kuota, sisa_kuota FROM tipe_tiket WHERE event_id_event = %s;"
    tipe_tikets = execute_query(query_tipe_tiket, (str(selected_event_id),), fetch_all=True)

    if tipe_tikets:
        print("\nTipe Tiket yang tersedia:")
        print(f"{'No.':<5} | {'Nama Tipe':<20} | {'Harga':<10} | {'Kuota':<8} | {'Sisa':<8}")
        print("-" * 60)
        for i, tt in enumerate(tipe_tikets):
            print(f"{i+1:<5} | {tt[1]:<20} | {tt[2]:<10.2f} | {tt[3]:<8} | {tt[4]:<8}")
        print("-" * 60)

        while True:
            action = input("Pilih aksi untuk tipe tiket (edit/tambah/hapus/selesai): ").lower()
            if action == 'edit':
                try:
                    pilihan_tipe = int(input("Pilih nomor tipe tiket yang ingin diedit: "))
                    if 1 <= pilihan_tipe <= len(tipe_tikets):
                        selected_tipe_id = tipe_tikets[pilihan_tipe-1][0]
                        current_nama = tipe_tikets[pilihan_tipe-1][1]
                        current_harga = tipe_tikets[pilihan_tipe-1][2]
                        current_kuota = tipe_tikets[pilihan_tipe-1][3]
                        current_sisa_kuota = tipe_tikets[pilihan_tipe-1][4]

                        new_nama = input(f"Nama Tipe ({current_nama}): ") or current_nama
                        new_harga_str = input(f"Harga ({current_harga:.2f}): ")
                        new_harga = float(new_harga_str) if new_harga_str else current_harga
                        new_kuota_str = input(f"Kuota ({current_kuota}): ")
                        new_kuota = int(new_kuota_str) if new_kuota_str else current_kuota

                        sisa_diff = new_kuota - current_kuota
                        new_sisa_kuota = current_sisa_kuota + sisa_diff
                        if new_sisa_kuota < 0:
                            print("Sisa kuota tidak bisa negatif. Sesuaikan kuota baru.")
                            continue

                        query_update_tipe = """
                        UPDATE tipe_tiket
                        SET nama_tipe = %s, harga = %s, kuota = %s, sisa_kuota = %s
                        WHERE id_tipe_tiket = %s;
                        """
                        if execute_query(query_update_tipe, (new_nama, new_harga, new_kuota, new_sisa_kuota, selected_tipe_id)):
                            print("Tipe tiket berhasil diperbarui.")
                        else:
                            print("Gagal memperbarui tipe tiket.")
                    else:
                        print("Pilihan tidak valid.")
                except ValueError:
                    print("Input tidak valid.")
            elif action == 'tambah':
                nama_tipe = input("Nama Tipe Tiket baru: ")
                try:
                    harga = float(input("Harga Tiket baru: "))
                    kuota = int(input("Kuota Tiket baru: "))
                    if harga <= 0 or kuota <= 0:
                        print("Harga dan kuota harus lebih dari nol.")
                        continue
                except ValueError:
                    print("Harga atau kuota tidak valid.")
                    continue
                query_tipe_tiket = """
                INSERT INTO tipe_tiket (nama_tipe, harga, kuota, sisa_kuota, event_id_event)
                VALUES (%s, %s, %s, %s, %s);
                """
                if execute_query(query_tipe_tiket, (nama_tipe, harga, kuota, kuota, str(selected_event_id))):
                    print(f"Tipe tiket '{nama_tipe}' berhasil ditambahkan.")
                else:
                    print(f"Gagal menambahkan tipe tiket '{nama_tipe}'.")
                tipe_tikets = execute_query(query_tipe_tiket, (str(selected_event_id),), fetch_all=True)

            elif action == 'hapus':
                try:
                    pilihan_tipe = int(input("Pilih nomor tipe tiket yang ingin dihapus: "))
                    if 1 <= pilihan_tipe <= len(tipe_tikets):
                        selected_tipe_id = tipe_tikets[pilihan_tipe-1][0]
                        query_check_tickets = "SELECT COUNT(*) FROM tiket WHERE id_tipe_tiket = %s;"
                        ticket_count = execute_query(query_check_tickets, (selected_tipe_id,), fetch_one=True)[0]
                        if ticket_count > 0:
                            print(f"Tidak dapat menghapus tipe tiket ini karena ada {ticket_count} tiket yang terkait.")
                        else:
                            query_delete_tipe = "DELETE FROM tipe_tiket WHERE id_tipe_tiket = %s;"
                            if execute_query(query_delete_tipe, (selected_tipe_id,)):
                                print("Tipe tiket berhasil dihapus.")
                                tipe_tikets = execute_query(query_tipe_tiket, (str(selected_event_id),), fetch_all=True)
                            else:
                                print("Gagal menghapus tipe tiket.")
                    else:
                        print("Pilihan tidak valid.")
                except ValueError:
                    print("Input tidak valid.")
            elif action == 'selesai':
                break
            else:
                print("Aksi tidak valid.")
    else:
        print("Tidak ada tipe tiket untuk event ini. Anda bisa menambahkannya.")
        while True:
            add_new = input("Apakah Anda ingin menambahkan tipe tiket baru? (ya/tidak): ").lower()
            if add_new == 'ya':
                nama_tipe = input("Nama Tipe Tiket baru: ")
                try:
                    harga = float(input("Harga Tiket baru: "))
                    kuota = int(input("Kuota Tiket baru: "))
                    if harga <= 0 or kuota <= 0:
                        print("Harga dan kuota harus lebih dari nol.")
                        continue
                except ValueError:
                    print("Harga atau kuota tidak valid.")
                    continue
                query_tipe_tiket = """
                INSERT INTO tipe_tiket (nama_tipe, harga, kuota, sisa_kuota, event_id_event)
                VALUES (%s, %s, %s, %s, %s);
                """
                if execute_query(query_tipe_tiket, (nama_tipe, harga, kuota, kuota, str(selected_event_id))):
                    print(f"Tipe tiket '{nama_tipe}' berhasil ditambahkan.")
                else:
                    print(f"Gagal menambahkan tipe tiket '{nama_tipe}'.")
            else:
                break
    menu_penyelenggara()


def hapus_karya():
    if not current_user_id or current_user_role != 'penyelenggara':
        print("Anda harus login sebagai penyelenggara untuk menghapus karya.")
        return

    events = lihat_karya()
    if not events:
        print("Tidak ada karya yang bisa dihapus.")
        menu_penyelenggara()
        return

    try:
        pilihan = int(input("Pilih nomor karya yang ingin dihapus: "))
        if 1 <= pilihan <= len(events):
            selected_event_id = events[pilihan-1][0]
            selected_event_title = events[pilihan-1][1]
        else:
            print("Pilihan tidak valid.")
            menu_penyelenggara()
            return
    except ValueError:
        print("Input tidak valid. Masukkan nomor.")
        menu_penyelenggara()
        return

    konfirmasi = input(f"Anda yakin ingin menghapus '{selected_event_title}' dan semua data terkait? (ya/tidak): ").lower()
    if konfirmasi != 'ya':
        print("Penghapusan dibatalkan.")
        menu_penyelenggara()
        return

    try:
        conn.autocommit = False

        query_get_order_ids = """
        SELECT o.id_order
        FROM orders o
        JOIN order_items oi ON o.id_order = oi.id_order
        JOIN tipe_tiket tt ON oi.id_tipe_tiket = tt.id_tipe_tiket
        WHERE tt.event_id_event = %s;
        """
        order_ids_for_event = execute_query(query_get_order_ids, (str(selected_event_id),), fetch_all=True)
        
        if order_ids_for_event:
            for order_id_tuple in order_ids_for_event:
                order_id = order_id_tuple[0]
                execute_query("DELETE FROM tiket WHERE id_order = %s;", (str(order_id),))
                execute_query("DELETE FROM order_items WHERE id_order = %s;", (str(order_id),))
                execute_query("DELETE FROM orders WHERE id_order = %s;", (str(order_id),))

        execute_query("DELETE FROM tipe_tiket WHERE event_id_event = %s;", (str(selected_event_id),))

        execute_query("DELETE FROM event WHERE id_event = %s;", (str(selected_event_id),))

        conn.commit()
        print(f"Karya '{selected_event_title}' dan semua data terkait berhasil dihapus.")

    except psycopg2.Error as e:
        conn.rollback()
        print(f"Gagal menghapus karya: {e}")
    finally:
        conn.autocommit = True
    menu_penyelenggara()

def tambah_voucher():
    if not current_user_id or current_user_role != 'penyelenggara':
        print("Anda harus login sebagai penyelenggara untuk menambah voucher.")
        return

    print("\n--- Tambah Voucher Baru ---")
    kode_voucher = input("Kode Voucher: ")
    
    jenis_diskon = ''
    while jenis_diskon not in JENIS_DISKON_ENUM:
        jenis_diskon = input(f"Jenis Diskon ({', '.join(JENIS_DISKON_ENUM)}): ").lower()
        if jenis_diskon not in JENIS_DISKON_ENUM:
            print("Jenis diskon tidak valid. Silakan pilih dari opsi yang tersedia.")

    try:
        nilai_diskon = float(input("Nilai Diskon (misal: 10 untuk 10%, atau 50000 untuk nominal): "))
        if nilai_diskon <= 0:
            print("Nilai diskon harus lebih dari nol.")
            menu_penyelenggara()
            return
    except ValueError:
        print("Nilai diskon tidak valid.")
        menu_penyelenggara()
        return

    tanggal_mulai_str = input("Tanggal Mulai Berlaku (YYYY-MM-DD HH:MM): ")
    tanggal_kadaluwarsa_str = input("Tanggal Kadaluwarsa (YYYY-MM-DD HH:MM): ")
    
    try:
        tanggal_mulai_berlaku = datetime.datetime.strptime(tanggal_mulai_str, '%Y-%m-%d %H:%M')
        tanggal_mulai_berlaku = pytz.timezone('Asia/Jakarta').localize(tanggal_mulai_berlaku)
        tanggal_kadaluwarsa = datetime.datetime.strptime(tanggal_kadaluwarsa_str, '%Y-%m-%d %H:%M')
        tanggal_kadaluwarsa = pytz.timezone('Asia/Jakarta').localize(tanggal_kadaluwarsa)

        if tanggal_kadaluwarsa <= tanggal_mulai_berlaku:
            print("Tanggal kadaluwarsa harus setelah tanggal mulai berlaku.")
            menu_penyelenggara()
            return
        if tanggal_kadaluwarsa <= datetime.datetime.now(pytz.timezone('Asia/Jakarta')):
            print("Tanggal kadaluwarsa harus di masa depan.")
            menu_penyelenggara()
            return

    except ValueError:
        print("Format tanggal salah. Gunakan YYYY-MM-DD HH:MM.")
        menu_penyelenggara()
        return

    try:
        kuota = int(input("Kuota Voucher: "))
        if kuota <= 0:
            print("Kuota voucher harus lebih dari nol.")
            menu_penyelenggara()
            return
    except ValueError:
        print("Kuota voucher tidak valid.")
        menu_penyelenggara()
        return

    query = """
    INSERT INTO vouchers (kode_voucher, jenis_diskon, nilai_diskon,
                          tanggal_mulai_berlaku, tanggal_kadaluwarsa, kuota, sisa_kuota)
    VALUES (%s, %s, %s, %s, %s, %s, %s);
    """
    if execute_query(query, (kode_voucher, jenis_diskon, nilai_diskon,
                             tanggal_mulai_berlaku, tanggal_kadaluwarsa, kuota, kuota)):
        print(f"Voucher '{kode_voucher}' berhasil ditambahkan!")
    else:
        print("Gagal menambahkan voucher. Mungkin kode voucher sudah ada.")
    menu_penyelenggara()

def cari_karya_keyword():
    print("\n--- Cari Karya ---")
    keyword = input("Masukkan kata kunci (judul/deskripsi): ")
    query = """
    SELECT e.id_event, e.judul_event, e.tanggal_mulai_event, e.lokasi, u.nama_lengkap
    FROM event e
    JOIN "user" u ON e.user_id_user = u.id_user
    WHERE LOWER(e.judul_event) LIKE %s OR LOWER(e.deskripsi_event) LIKE %s
    ORDER BY e.tanggal_mulai_event DESC;
    """
    search_pattern = f"%{keyword.lower()}%"
    events = execute_query(query, (search_pattern, search_pattern), fetch_all=True)

    if not events:
        print("Tidak ada karya yang ditemukan dengan kata kunci tersebut.")
        menu_penikmat()
        return

    print(f"\n--- Hasil Pencarian untuk '{keyword}' ---")
    print(f"{'No.':<5} | {'Judul Event':<30} | {'Tanggal Mulai':<20} | {'Lokasi':<25} | {'Penyelenggara':<20}")
    print("-" * 105)
    for i, event in enumerate(events):
        print(f"{i+1:<5} | {event[1]:<30} | {event[2].strftime('%Y-%m-%d %H:%M'):<20} | {event[3]:<25} | {event[4]:<20}")
    print("-" * 105)

    try:
        pilihan = int(input("Pilih nomor karya untuk melihat detail (0 untuk batal): "))
        if 1 <= pilihan <= len(events):
            selected_event_id = events[pilihan-1][0]
            tampilkan_detail_event(selected_event_id)
        elif pilihan == 0:
            print("Pencarian dibatalkan.")
            menu_penikmat()
        else:
            print("Pilihan tidak valid.")
            menu_penikmat()
    except ValueError:
        print("Input tidak valid. Masukkan nomor.")
        menu_penikmat()

def tampilkan_detail_event(event_id):
    query_event = """
    SELECT e.judul_event, e.deskripsi_event, e.tanggal_mulai_event, e.tanggal_selesai_event,
           e.lokasi, e.poster_event, u.nama_lengkap
    FROM event e
    JOIN "user" u ON e.user_id_user = u.id_user
    WHERE e.id_event = %s;
    """
    event_detail = execute_query(query_event, (str(event_id),), fetch_one=True)

    if not event_detail:
        print("Event tidak ditemukan.")
        menu_penikmat()
        return

    print(f"\n--- Detail Event: {event_detail[0]} ---")
    print(f"Judul: {event_detail[0]}")
    print(f"Deskripsi: {event_detail[1] if event_detail[1] else '-'}")
    print(f"Tanggal Mulai: {event_detail[2].strftime('%Y-%m-%d %H:%M')}")
    print(f"Tanggal Selesai: {event_detail[3].strftime('%Y-%m-%d %H:%M') if event_detail[3] else '-'}")
    print(f"Lokasi: {event_detail[4]}")
    print(f"Poster: {event_detail[5] if event_detail[5] else '-'}")
    print(f"Penyelenggara: {event_detail[6]}")

    print("\n--- Tipe Tiket Tersedia ---")
    query_tipe_tiket = """
    SELECT id_tipe_tiket, nama_tipe, harga, kuota, sisa_kuota
    FROM tipe_tiket
    WHERE event_id_event = %s AND sisa_kuota > 0
    ORDER BY harga ASC;
    """
    tipe_tikets = execute_query(query_tipe_tiket, (str(event_id),), fetch_all=True)

    if not tipe_tikets:
        print("Tidak ada tipe tiket yang tersedia untuk event ini atau kuota habis.")
        menu_penikmat()
        return

    print(f"{'No.':<5} | {'Nama Tipe':<20} | {'Harga':<15} | {'Sisa Kuota':<12}")
    print("-" * 55)
    for i, tt in enumerate(tipe_tikets):
        print(f"{i+1:<5} | {tt[1]:<20} | Rp {tt[2]:<12.2f} | {tt[4]:<12}")
    print("-" * 55)

    menu_order(event_id, tipe_tikets)

def menu_order(event_id, available_ticket_types):
    if not current_user_id or current_user_role != 'user':
        print("Anda harus login sebagai penikmat untuk memesan tiket.")
        menu_penikmat()
        return

    print("\n--- Menu Pemesanan Tiket ---")
    try:
        pilihan_tipe = int(input("Pilih nomor tipe tiket yang ingin dibeli (0 untuk batal): "))
        if pilihan_tipe == 0:
            print("Pemesanan dibatalkan.")
            menu_penikmat()
            return
        if not (1 <= pilihan_tipe <= len(available_ticket_types)):
            print("Pilihan tipe tiket tidak valid.")
            menu_penikmat()
            return

        selected_tipe = available_ticket_types[pilihan_tipe-1]
        id_tipe_tiket = selected_tipe[0]
        nama_tipe = selected_tipe[1]
        harga_per_tiket = selected_tipe[2]
        sisa_kuota = selected_tipe[4]

        kuantitas = int(input(f"Masukkan jumlah tiket '{nama_tipe}' yang ingin dibeli (maks {sisa_kuota}): "))
        if kuantitas <= 0 or kuantitas > sisa_kuota:
            print("Kuantitas tidak valid atau melebihi kuota yang tersedia.")
            menu_penikmat()
            return

        sub_total = harga_per_tiket * kuantitas
        total_harga = sub_total
        voucher_id = None
        nilai_diskon_terpakai = 0

        gunakan_voucher = input("Apakah Anda memiliki kode voucher? (ya/tidak): ").lower()
        if gunakan_voucher == 'ya':
            kode_voucher = input("Masukkan kode voucher: ")
            query_voucher = """
            SELECT id_voucher, jenis_diskon, nilai_diskon, tanggal_kadaluwarsa, sisa_kuota
            FROM vouchers
            WHERE kode_voucher = %s AND tanggal_kadaluwarsa > CURRENT_TIMESTAMP AND sisa_kuota > 0;
            """
            voucher_detail = execute_query(query_voucher, (kode_voucher,), fetch_one=True)

            if voucher_detail:
                voucher_id = voucher_detail[0]
                jenis_diskon = voucher_detail[1]
                nilai_diskon = float(voucher_detail[2])

                if jenis_diskon == 'persentase':
                    diskon_amount = sub_total * (nilai_diskon / 100)
                    total_harga -= diskon_amount
                    nilai_diskon_terpakai = diskon_amount
                    print(f"Voucher '{kode_voucher}' diterapkan. Diskon {nilai_diskon}% (Rp {diskon_amount:.2f}).")
                elif jenis_diskon == 'nominal':
                    total_harga -= nilai_diskon
                    nilai_diskon_terpakai = nilai_diskon
                    print(f"Voucher '{kode_voucher}' diterapkan. Diskon Rp {nilai_diskon:.2f}.")
                
                if total_harga < 0:
                    total_harga = 0
            else:
                print("Kode voucher tidak valid, sudah kadaluwarsa, atau kuota habis.")

        print(f"\n--- Ringkasan Pesanan ---")
        print(f"Event: {execute_query('SELECT judul_event FROM event WHERE id_event = %s', (str(event_id),), fetch_one=True)[0]}")
        print(f"Tipe Tiket: {nama_tipe}")
        print(f"Kuantitas: {kuantitas}")
        print(f"Harga per tiket: Rp {harga_per_tiket:.2f}")
        print(f"Sub Total: Rp {sub_total:.2f}")
        if voucher_id:
            print(f"Diskon Voucher: Rp {nilai_diskon_terpakai:.2f}")
        print(f"Total Harga Akhir: Rp {total_harga:.2f}")

        metode_pembayaran_str = input(f"Pilih metode pembayaran ({', '.join(METODE_BAYAR_ENUM)}): ").lower()
        if metode_pembayaran_str not in METODE_BAYAR_ENUM:
            print("Metode pembayaran tidak valid.")
            menu_penikmat()
            return

        konfirmasi = input("Konfirmasi pesanan? (ya/tidak): ").lower()
        if konfirmasi != 'ya':
            print("Pemesanan dibatalkan.")
            menu_penikmat()
            return

        conn.autocommit = False
        try:
            order_id = uuid.uuid4()
            kode_pembayaran = f"PAY-{uuid.uuid4().hex[:8].upper()}"

            query_insert_order = """
            INSERT INTO orders (id_order, tanggal_order, total_harga, status_pembayaran,
                                metode_pembayaran, kode_pembayaran, user_id_user, vouchers_id_voucher)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
            """
            execute_query(query_insert_order, (str(order_id), datetime.datetime.now(pytz.timezone('Asia/Jakarta')),
                                               total_harga, 'menunggu_pembayaran', metode_pembayaran_str,
                                               kode_pembayaran, str(current_user_id), voucher_id))

            query_insert_order_item = """
            INSERT INTO order_items (kuantitas, harga_beli, id_order, id_tipe_tiket)
            VALUES (%s, %s, %s, %s);
            """
            execute_query(query_insert_order_item, (kuantitas, harga_per_tiket, str(order_id), id_tipe_tiket))

            query_update_tipe_kuota = """
            UPDATE tipe_tiket
            SET sisa_kuota = sisa_kuota - %s
            WHERE id_tipe_tiket = %s;
            """
            execute_query(query_update_tipe_kuota, (kuantitas, id_tipe_tiket))

            if voucher_id:
                query_update_voucher_kuota = """
                UPDATE vouchers
                SET sisa_kuota = sisa_kuota - 1
                WHERE id_voucher = %s;
                """
                execute_query(query_update_voucher_kuota, (voucher_id,))

            for _ in range(kuantitas):
                ticket_code = uuid.uuid4()
                query_insert_ticket = """
                INSERT INTO tiket (kode_tiket, status_tiket, id_order, id_tipe_tiket)
                VALUES (%s, %s, %s, %s);
                """
                execute_query(query_insert_ticket, (str(ticket_code), 'aktif', str(order_id), id_tipe_tiket))

            conn.commit()
            print("\n--- Pesanan Berhasil Dibuat! ---")
            print(f"ID Pesanan Anda: {order_id}")
            print(f"Kode Pembayaran: {kode_pembayaran}")
            print("Silakan selesaikan pembayaran. Tiket Anda akan aktif setelah pembayaran dikonfirmasi.")

        except psycopg2.Error as e:
            conn.rollback()
            print(f"Terjadi kesalahan saat memproses pesanan: {e}")
        finally:
            conn.autocommit = True
    except ValueError:
        print("Input tidak valid. Silakan coba lagi.")
    menu_penikmat()

def tampilan_penyelenggara():
    print("\n--- Selamat datang di menu penyelenggara! ---")
    print("1. Login")
    print("2. Registrasi")
    print("3. Keluar")
    pilihan = input("Pilih menu: ")
    if pilihan == "1":
        if login_penyelenggara():
            menu_penyelenggara()
        else:
            tampilan_penyelenggara()
    elif pilihan == "2":
        if registrasi_penyelenggara():
            if login_penyelenggara():
                menu_penyelenggara()
            else:
                tampilan_penyelenggara()
        else:
            tampilan_penyelenggara()
    elif pilihan == "3":
        print("Keluar dari akun penyelenggara.")
        tampilan_awal()
    else:
        print("Pilihan tidak valid. Silakan coba lagi.")
        tampilan_penyelenggara()

def tampilan_penikmat():
    print("\n--- Selamat datang di menu penikmat! ---")
    print("1. Login")
    print("2. Registrasi")
    print("3. Keluar")
    pilihan = input("Pilih menu: ")
    if pilihan == "1":
        if login_penikmat():
            menu_penikmat()
        else:
            tampilan_penikmat()
    elif pilihan == "2":
        if registrasi_penikmat():
            if login_penikmat():
                menu_penikmat()
            else:
                tampilan_penikmat()
        else:
            tampilan_penikmat()
    elif pilihan == "3":
        print("Keluar dari akun penikmat.")
        tampilan_awal()
    else:
        print("Pilihan tidak valid. Silakan coba lagi.")
        tampilan_penikmat()

def menu_penyelenggara():
    global current_user_id, current_user_role, current_user_name
    if not current_user_id or current_user_role != 'penyelenggara':
        print("Anda tidak login sebagai penyelenggara. Kembali ke menu utama.")
        tampilan_awal()
        return

    print(f"\n--- Menu Penyelenggara ({current_user_name}) ---")
    print("1. Tambah Karya")
    print("2. Lihat Karya Saya")
    print("3. Edit Karya")
    print("4. Hapus Karya")
    print("5. Tambah Voucher")
    print("6. Logout")
    pilihan = input("Pilih menu: ")
    if pilihan == "1":
        tambah_karya()
    elif pilihan == "2":
        lihat_karya(show_all=False)
        input("Tekan Enter untuk kembali...")
        menu_penyelenggara()
    elif pilihan == "3":
        edit_karya()
    elif pilihan == "4":
        hapus_karya()
    elif pilihan == "5":
        tambah_voucher()
    elif pilihan == "6":
        current_user_id = None
        current_user_role = None
        current_user_name = None
        print("Anda telah logout.")
        tampilan_awal()
    else:
        print("Pilihan tidak valid. Silakan coba lagi.")
        menu_penyelenggara()

def menu_penikmat():
    global current_user_id, current_user_role, current_user_name
    if not current_user_id or current_user_role != 'user':
        print("Anda tidak login sebagai penikmat. Kembali ke menu utama.")
        tampilan_awal()
        return

    print(f"\n--- Menu Penikmat ({current_user_name}) ---")
    print("1. Lihat Semua Karya")
    print("2. Cari Karya")
    print("3. Logout")
    pilihan = input("Pilih menu: ")
    if pilihan == "1":
        events = lihat_karya(show_all=True)
        if events:
            try:
                pilihan_detail = int(input("Pilih nomor karya untuk melihat detail (0 untuk batal): "))
                if 1 <= pilihan_detail <= len(events):
                    selected_event_id = events[pilihan_detail-1][0]
                    tampilkan_detail_event(selected_event_id)
                elif pilihan_detail == 0:
                    print("Kembali ke menu penikmat.")
                    menu_penikmat()
                else:
                    print("Pilihan tidak valid.")
                    menu_penikmat()
            except ValueError:
                print("Input tidak valid. Masukkan nomor.")
                menu_penikmat()
        else:
            menu_penikmat()
    elif pilihan == "2":
        cari_karya_keyword()
    elif pilihan == "3":
        current_user_id = None
        current_user_role = None
        current_user_name = None
        print("Anda telah logout.")
        tampilan_awal()
    else:
        print("Pilihan tidak valid. Silakan coba lagi.")
        menu_penikmat()

def pilih_role():
    print("\n--- Pilih Peran Anda ---")
    print("1. Penyelenggara Karya")
    print("2. Penikmat Karya")
    print("3. Keluar Aplikasi")
    pilihan = input("Pilih menu: ")
    if pilihan == "1":
        tampilan_penyelenggara()
    elif pilihan == "2":
        tampilan_penikmat()
    elif pilihan == "3":
        print("Terima kasih telah menggunakan Gelora - Pagelaran Karya!")
        close_db()
        exit()
    else:
        print("Pilihan tidak valid. Silakan coba lagi.")
        pilih_role()

def tampilan_awal():
    print("\n========================================")
    print("Selamat datang di Gelora - Pagelaran Karya!")
    print("========================================")
    pilih_role()

if __name__ == "__main__":
    connect_db()

    try:
        cur.execute("INSERT INTO roles (id_role, nama_role) VALUES (1, 'penyelenggara') ON CONFLICT (id_role) DO NOTHING;")
        cur.execute("INSERT INTO roles (id_role, nama_role) VALUES (2, 'user') ON CONFLICT (id_role) DO NOTHING;")
        conn.commit()
        print("Role 'penyelenggara' dan 'user' dipastikan ada di database.")
    except psycopg2.Error as e:
        print(f"Gagal memastikan role ada: {e}")
        conn.rollback()

    if conn:
        tampilan_awal()
    else:
        print("Aplikasi tidak dapat berjalan tanpa koneksi database.")
        close_db()