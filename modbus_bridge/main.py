from ModbusBorunteClient import ModbusBorunteClient, ModbusBorunteError
import time

def main():
    robot1 = ModbusBorunteClient(host="192.168.101.21", name_id="borunte_01", port=502)
    robot1.connect()
    print("Robot 1 connected")
    robot2 = ModbusBorunteClient(host="192.168.101.22", name_id="borunte_02", port=503)
    robot2.connect()
    print("Robot 2 connected")
    # read all status each 4 seconds
    while True:
        try:
            status1 = robot1.read_borunte_data_all()
            status2 = robot2.read_borunte_data_all()
            print("STATUS 01 : ",status1)
            print("STATUS 02 : ", status2)
        except ModbusBorunteError as e:
            print(f"Error: {e}")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            time.sleep(4)


if __name__ == "__main__":
    main()