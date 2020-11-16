import bluepy
import numpy as np
import ipget
import matplotlib.pyplot as plt
import pprint
import time
import os
import datetime
import csv
import sys
from concurrent.futures import ThreadPoolExecutor

from oauth2client.service_account import ServiceAccountCredentials
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
#=====================================================================
def input_param():
    global data_count ,search_count ,scan_time, cycle_time, scatter_xtick
    while True:
        try:
            data_count = int(input("測定回数を入力： "))
            search_count = int(input("bluetooth deviceのsearch回数を入力： "))
            scan_time = float(input("RSSI測定のscan time[s]を入力： "))
            cycle_time = int(input("何秒毎の測定かのcycle time[μs]を入力： "))
            scatter_xtick = int(input("散布図のx軸目盛の幅を入力： "))
            startOrNot = input("測定を開始しますか？　y/n \n")
            if startOrNot == "y":
                break
            elif startOrNot == "n":
                print("もう一度入力してください　\n")
                print("Ctrl + c:プログラム終了　\n")
                pass
            else:
                print("もう一度入力してください　\n")
                pass

        except Exception as e:
            print(e, "\n")
            print("もう一度入力してください　\n")
            pass
        except KeyboardInterrupt:
            sys.exit()
#=====================================================================
def Search_btAddr(saerch_count, scan_time):
    list = ["time", ]
    global scanner
    scanner = bluepy.btle.Scanner(0)
    for i in range(search_count):
        devices = scanner.scan(scan_time)
        for device in devices:
            if 'b8:27:eb' in device.addr:
                if str(device.addr)  not in list:
                    list.append(str(device.addr))
    return(list)
#=====================================================================
def remaining_timer(result, remaining_t):
    count_time = remaining_t
    base_time = round(time.time(),1)
    #print(base_time)
    while result == True:
        try:
            now_time = round(time.time(),1)
            #print(now_time)
            deltaTime = count_time - (now_time - base_time)
            print("device search 残り", round(deltaTime,1), "s")
            if deltaTime <= 0:
                break
            time.sleep(0.498)
        except KeyboardInterrupt:
            sys.exit()
#=====================================================================
def Scan_RSSI(list, scan_time, dtime):
    devices, count = scanner.scan(scan_time), 0
    return_list = [np.nan] * len(list)
    return_list[0] = dtime
    for device in devices:
        if device.addr in list:
            return_list[list.index(device.addr)] = str(device.rssi)
    print(dtime, [i for i in return_list])
    return(return_list)
#=====================================================================
def Judge_Scan(count, scan_time, cycle_time,error_count, data_list, addr_list):
    base_time = round(time.time(),1)
    deltatime = 0
    while True:
        dt_now = datetime.datetime.now()
        """
        if dt_now.second % cycle_time == 0:
            try:
                print("残り", count, " スキャン中")
                data_list.append(Scan_RSSI(addr_list, scan_time, str(dt_now)[11:19]))
                if count == 1:
                    break
                count -= 1
            except Exception as e:
                #traceback.print_exc()
                print(e)
                print("Error (count=" + str(error_count) + ")")
                error_count += 1
                if error_count == 10:
                    break
                os.system("sudo systemctl daemon-reload")
                print("Retry")
                pass
            except KeyboardInterrupt:
                break
        """
        #now_time = round(time.time(),1)
        #deltatime = now_time - base_time
        if deltatime % cycle_time == 0:
            print(deltatime)
            try:
                print("残り", count, " スキャン中")
                data_list.append(Scan_RSSI(addr_list, scan_time, str(deltatime)))
                if count == 1:
                    break
                count -= 1
            except Exception as e:
                #traceback.print_exc()
                print(e)
                print("Error (count=" + str(error_count) + ")")
                error_count += 1
                if error_count == 10:
                    break
                os.system("sudo systemctl daemon-reload")
                print("Retry")
                pass
            except KeyboardInterrupt:
                sys.exit()

        now_time = round(time.time(),1)
        deltatime = now_time - base_time
    print("測定終了 \n")
    return(data_list)

#=====================================================================
def IPget():    #IPアドレスの取得
    a = ipget.ipget()
    ipaddr = str(a.ipaddr("eth0"))
    return(ipaddr)
#=====================================================================
def save_file(name, data_list):
    try:
        print("save as csv ...")
        with open(name, "w") as f:  #リストをcsvファイルにする
            writer = csv.writer(f, lineterminator="\n")
            writer.writerows(data_list)
        print("success! \n")
    except Exception as e:
        #traceback.print_exc()
        print(e)
        pass
#=====================================================================
def G_upload_scanData(local_file, gdrive_dir , name):
    print("Start Upload")
    for i in range(2):
        try:
            gauth = GoogleAuth()
            gauth.LocalWebserverAuth()
            drive = GoogleDrive(gauth)
            folder_id = drive.ListFile({'q': 'title = "{}"'.format(gdrive_dir)}).GetList()[0]['id']
            f = drive.CreateFile({"parents": [{"id": folder_id}]})
            f.SetContentFile(local_file)
            f['title'] = name
            f.Upload()
            print("success! \n")
        except Exception as e:
            #traceback.print_exc()
            print(e)
            print("Error (count=" + str(i+1) + ")")
            time.sleep(3.0)
            print("Retry")
            pass
        else:
            break
    else:
        print("failure...")
        pass
#=====================================================================
def G_upload_ScatterFig(local_file, gdrive_dir, scatter_name):
    print("Start Upload")
    for i in range(2):
        try:
            gauth = GoogleAuth()
            gauth.CommandLineAuth()
            drive = GoogleDrive(gauth)
            folder_id = drive.ListFile({'q': 'title = "{}"'.format(gdrive_dir)}).GetList()[0]['id']
            f = drive.CreateFile({'mimeType': 'image/png',
                                  'parents': [{'id':folder_id}]})
            f['title'] = scatter_name
            f.SetContentFile(local_file)
            f.Upload()
            print("success!")
        except Exception as e:
            traceback.print_exc()
            print(e)
            print("Error (count=" + str(i+1) + ")")
            time.sleep(3.0)
            print("Retry")
            pass
        else:
            break
    else:
        print("failure...")
        pass
#=====================================================================

if __name__ == '__main__':
    #mklist_list = [1, 4]   #[searh回数, scan秒数]
    Error_count = 0

    input_param()
    mklist_list = [search_count, scan_time]      #[デバイスのsearh回数, scanする秒数]
    scatter_lim_num = data_count

    dt_start = datetime.datetime.now()
    print(dt_start)
    print("start \n")

    remaining_time = mklist_list[0]*mklist_list[1]
    print("making a device list,  please wait about" ,remaining_time, "second")
    executor = ThreadPoolExecutor(max_workers=2)    #並列処理のためのスレッドを作成
    addr_list_info = []    #デバイススキャン側のスレッド情報を格納するList

    addr_list = executor.submit(Search_btAddr, mklist_list[0], mklist_list[1])
    addr_list_info.append(addr_list) #デバイススキャンの情報をListに追加

    executor.submit(remaining_timer, addr_list.running(), remaining_time)

    executor.shutdown()    #スレッドを閉じる

    print(addr_list.result(), "\n")

    try:
        data_list = [addr_list.result(), ]    #スレッドで実行した結果を格納
        pprint.pprint(data_list)
        print()

        ipaddr = IPget()
        #print(ipaddr,"\n")
        dt_now = datetime.datetime.now()
        name =  str(dt_now.year) + "_" + str(dt_now.month) + str(dt_now.day) + "_" + str(dt_now.hour) + str(dt_now.minute) + "_" + ipaddr[:-2] + ".csv"
        path = "ScanData/" + name
        save_file(path, data_list)

        G_upload_scanData(path, "bluetooth_data", name) #scanしたデータをアップロード


        print("making scatter...")

        data_list_t = list(zip(*data_list))
        x_data = data_list_t[0]

        plt.rcParams['font.family'] ='sans-serif'#使用するフォント
        plt.rcParams['xtick.major.width'] = 1.0#x軸主目盛り線の線幅
        plt.rcParams['ytick.major.width'] = 1.0#y軸主目盛り線の線幅
        plt.rcParams['xtick.direction'] = 'in'#x軸の目盛線が内向き('in')か外向き('out')か双方向か('inout')
        plt.rcParams['ytick.direction'] = 'in'#y軸の目盛線が内向き('in')か外向き('out')か双方向か('inout')
        plt.rcParams['font.size'] = 8 #フォントの大きさ
        plt.rcParams['axes.linewidth'] = 1.0# 軸の線幅edge linewidth。囲みの太さ

        for i in data_list_t[1:]:
            y_data = i[1:]
            fig, axs = plt.subplots(nrows = 1, ncols = 1, figsize = (10,8))
            x_data_ = [j + 1 for j in range(len(y_data))]
            y_data_ = [float(k) for k in y_data]

            xtick = range(0, scatter_lim_num + 1, scatter_xtick)
            # Max = np.nanmax(y_data_[1:]).astype(int)
            # Min = np.nanmin(y_data_[1:]).astype(int)
            # ytick = range(Max + 2, Min - 2, -2)
            ytick = range(-15, -85, -5)
            axs.set_xticks(xtick)
            axs.set_yticks(ytick)
            axs.set_xlim(0, scatter_lim_num + 5)
            axs.set_ylim(-85,-15)
            axs.scatter(x_data_, y_data_, s = 25, marker = "o")
            plt.tight_layout()

            scatter_title = i[0] + "  rssi  (" + x_data[1] + " ~~ " + x_data[-1] + ")"
            axs.set_title(scatter_title)
            axs.set_xlabel("count [times]")
            axs.set_ylabel("rssi [dBm]")

            scatter_name = scatter_title + "_" + ipaddr[:-2] + ".png"
            scatter_path = "TestPngData/" + scatter_name
            fig.savefig(scatter_path)

            G_upload_ScatterFig(scatter_path, "bluetooth_data", scatter_name)


        dt_end = datetime.datetime.now()
        delta_time = dt_end - dt_start
        print()
        print(delta_time)
        print("Finish ! !")

    except KeyboardInterrupt:
        sys.exit()
