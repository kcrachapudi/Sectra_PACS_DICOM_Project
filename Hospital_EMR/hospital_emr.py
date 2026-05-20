import socket
import threading
import time

VT, FS, CR = b'\x0b', b'\x1c', b'\x0d'

def listen_for_results():
    """Simulates the hospital inbound port listening for Sectra's reports."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('127.0.0.1', 5555))
        s.listen(1)
        print("[Hospital EMR] Inbound interface listening on port 5555...")
        
        while True:
            conn, addr = s.accept()
            with conn:
                data = conn.recv(2048)
                if data:
                    clean_msg = data.replace(VT, b'').replace(FS, b'').decode('utf-8')
                    print("\n" + "#"*60)
                    print("[HOSPITAL EMR - NEW SCAN RESULT RECEIVED FROM SECTRA PACS]")
                    print(clean_msg.replace('\r', '\n'))
                    print("#"*60 + "\n")
                    break

def send_hl7_order():
    """Sends the initial X-ray order to Mirth."""
    time.sleep(1)
    hl7_msg = (
        "MSH|^~\\&|EPIC|HOSPITAL|SECTRA|PACS|202605191200||ORM^O01|MSG00002|P|2.3|" + "\r" +
        "PID|||999888^^^MRN||SMITH^JANE^||19850822|F|" + "\r" +
        "PV1||I|RAD-ROOM1||||5555^Dr^House||||||||||||VISIT88888|" + "\r" +
        "ORC|NW|ORD12345||||||202605191200|" + "\r" +
        "OBR|1|||RAD-CHEST^Chest X-Ray|||||||||||||||||||||O|"
    )
    payload = VT + hl7_msg.encode('utf-8') + FS + CR
    
    print("[Hospital EMR] Blasting X-Ray Order to Mirth on port 4444...")
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(('127.0.0.1', 4444))
            s.sendall(payload)
            response = s.recv(1024)
            print("[Hospital EMR] Success! Received MLLP ACK from Mirth.")
    except Exception as e:
        print(f"[Hospital EMR] Connection to Mirth failed: {e}")

if __name__ == "__main__":
    listener_thread = threading.Thread(target=listen_for_results, daemon=True)
    listener_thread.start()
    send_hl7_order()
    
    while listener_thread.is_alive():
        time.sleep(1)