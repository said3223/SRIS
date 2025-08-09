from sris_kernel import SRISChatApp
import tkinter as tk

if __name__ == "__main__":
    print("--- SRIS Kernel с GUI ---")
    print("--- Логи работы ядра будут выводиться в терминале. ---")
    print("--- Закройте окно GUI для завершения программы. ---")
    main_window = tk.Tk()
    app = SRISChatApp(main_window)
    main_window.mainloop()
    print("\n--- Программа SRIS завершена ---")

