# 项目名称
Data Tool

## 项目简介
该工具用于IMU设备调试，测试。
目前支持的通信接口：
1. Uart
目前支持的功能：
1. 串口数据的记录与解析。（支持的包类型有:S1, S2, S3, A1, FM, AT）
2. 串口数据实时可视化输出。
3. field配置。 (临时配置/永久配置)
4. 固件升级。（支持设备：IMU330BA）

## 安装说明
Python库：
matplotlib：$pip install -i https://pypi.tuna.tsinghua.edu.cn/simple matplotlib

curses: $pip install -i https://pypi.tuna.tsinghua.edu.cn/simple windows-curses

## 使用说明
程序运行后会生成以下界面，分别对应数据记录，数据解析，数据可视化，字段设置和固件升级五个功能，使用'↑'和'↓'进行选择，'enter'选中进入。

![Alt text](pic/UI.png)


以下是使用时需要注意的一些事项：
1. 在开始使用该工具前需要配置使用参数，如串口号，波特率等，配置方法为：
'Data Log/..'->'User Setting'/'Data Play'->'Data Setting'打开配置文件

![Alt text](pic/Setting.png)

在port name和baud rate都设置好的情况下若要更新其他设置参数，可以在以下界面中单击'A'进行自动更新

![Alt text](pic/Auto.png)

（配置文件中的'maxt'是可显示数据的最大时间长度，'dt'是数据刷新的频率）
在配置完成后保存并关闭文件即可。

2. 解析数据时需要将数据名称改为以下格式（若解析的数据为此工具记录则不需要修改名称）
'device name' _ 'packet type'.bin，如果还需要加以其他后缀用以数据标识，需要用' _ '将后缀隔开
例：'imu_S1_2008.bin'

3. 在field配置中，需要先输入待配置field的ID（可输入多个，每个ID间用空格隔开）

![Alt text](pic/enter_field_id.png)