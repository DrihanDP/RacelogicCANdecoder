# High Level Analyzer
# For more information and documentation, please go to https://support.saleae.com/extensions/high-level-analyzer-extensions

from saleae.analyzers import HighLevelAnalyzer, AnalyzerFrame, StringSetting, NumberSetting, ChoicesSetting
from saleae.data import GraphTimeDelta
import datetime
import struct

def most_common(lst):
    new_list = [round(x) for x in lst]
    return max(new_list, key=new_list.count)

# self.data_list = []
# self.frame_start_time = []
# self.frame_end_time = []
# first_301 = False

# High level analyzers must subclass the HighLevelAnalyzer class.
class Hla(HighLevelAnalyzer):
    temp_frame = None
    result_types = {
        'message_information': {
            'format': '{{data.info}}, {{data.input_type}}',
        },
        'error': {
            'format': 'Error!'
        }
    }
    
    def __init__(self):
        self.delay_ms = []
        self.undelay_utc = []
        self.speed_robot = []
        self.speed_vehico = []
        self.utc_count = 1
        self.first_301 = False
        self.data_list = []
        self.frame_start_time = []
        self.frame_end_time = []

    def decode(self, frame: AnalyzerFrame):
        global UTCTime, speed
        if frame.type == 'identifier_field':
            self.id = frame.data['identifier']
            if self.id == 769 and self.first_301 == False:
                self.id301_start_time = frame.start_time
                self.first_301 = True
            elif self.id == 771:
                self.id303_start_time = frame.start_time
            if self.id == 769 and self.first_301 == True:
                self.last301 = frame.start_time
            return AnalyzerFrame('message_information', frame.start_time, frame.end_time, {
                'info': 'ID',
                'input_type': hex(self.id),
            })
        # Actual data conversion
        if frame.type == "can_error":
            self.id = None
            self.data_list = []
            self.frame_start_time = []
            self.frame_end_time = []
            return AnalyzerFrame('message_information', frame.start_time, frame.end_time, {
                'error': 'Error!'
                })
        elif frame.type == "data_field":
            data_byte = hex(frame.data["data"][0])
            data_byte = data_byte[2:]
            if len(data_byte) == 1:
                new_data_byte = "0" + data_byte
                self.data_list.append(new_data_byte)
            else:
                self.data_list.append(data_byte)
            self.frame_start_time.append(frame.start_time)
            self.frame_end_time.append(frame.end_time)
            # 301
            if self.id == 769:
                if len(self.data_list) == 1:
                    return AnalyzerFrame('message_information', frame.start_time, frame.end_time, {
                            'info': 'Sats',
                            'input_type': int(self.data_list[0], 16),
                        })
                elif len(self.data_list) == 4:
                    hex_join = "".join(self.data_list[1:4])
                    converted_hex = int(hex_join, 16)
                    UTCTime = datetime.timedelta(seconds=(int(converted_hex) * 0.01))
                    return AnalyzerFrame('message_information', self.frame_start_time[1], self.frame_end_time[3], {
                            'info': 'UTC',
                            'input_type': str(UTCTime),
                        })
                elif len(self.data_list) == 8:
                    hex_join = "".join(self.data_list[4:])
                    converted_hex = int(hex_join, 16)
                    lat = converted_hex / 100000
                    last_start_time = self.frame_start_time[4]
                    last_end_time = self.frame_end_time[7]
                    self.data_list = []
                    self.frame_start_time = []
                    self.frame_end_time = []
                    return AnalyzerFrame('message_information', last_start_time, last_end_time, {
                            'info': 'Latitude',
                            'input_type': lat,
                        })
        # Converts 302 into longitude, speed, heading
            elif self.id == 770:
                if len(self.data_list) == 4:
                    hex_join = "".join(self.data_list[:4])
                    converted_hex = int(hex_join, 16)
                    long = converted_hex / 100000
                    return AnalyzerFrame('message_information', self.frame_start_time[0], self.frame_end_time[3], {
                            'info': 'Longitude',
                            'input_type': long,
                        })
                elif len(self.data_list) == 6:
                    hex_join = "".join(self.data_list[4:6])
                    converted_hex = int(hex_join, 16)
                    speed = converted_hex * 0.01 * 1.852 # convert knots to km/h
                    return AnalyzerFrame('message_information', self.frame_start_time[4], self.frame_end_time[5], {
                            'info': 'Speed',
                            'input_type': str(round(speed, 3)) + "km/h",
                        })
                elif len(self.data_list) == 8:
                    hex_join = "".join(self.data_list[6:])
                    converted_hex = int(hex_join, 16)
                    heading = converted_hex * 0.01
                    last_start_time = self.frame_start_time[6]
                    last_end_time = self.frame_end_time[7]
                    self.data_list = []
                    self.frame_start_time = []
                    self.frame_end_time = []
                    return AnalyzerFrame('message_information', last_start_time, last_end_time, {
                            'info': 'Heading',
                            'input_type': str(round(heading, 3)) + "°"
                        })
        # converts 303 into altitude, vertical velocity, addition info, status info
            elif self.id == 771:
                if len(self.data_list) == 3:
                    hex_join = "".join(self.data_list[:3])
                    converted_hex = int(hex_join, 16)
                    altitude = converted_hex * 0.01
                    return AnalyzerFrame('message_information', self.frame_start_time[0], self.frame_end_time[2], {
                            'info': 'Altitude',
                            'input_type': str(round(altitude, 3)) + "m",
                        })
                elif len(self.data_list) == 5:
                    hex_join = "".join(self.data_list[3:5])
                    converted_hex = int(hex_join, 16)
                    vertical_velocity = converted_hex * 0.01
                    return AnalyzerFrame('message_information', self.frame_start_time[3], self.frame_end_time[4], {
                            'info': 'Vertical Velocity',
                            'input_type': str(round(vertical_velocity, 3)) + "m/s",
                        })
                elif len(self.data_list) == 6:
                    return AnalyzerFrame('message_information', frame.start_time, frame.end_time, {
                            'info': 'Unused',
                            'input_type': 'N/A',
                        })
                elif len(self.data_list) == 7:
                    if self.data_list[6] == "04":
                        bit_info = "VBOX3"
                    elif self.data_list[6] == "08":
                        bit_info = "logging"
                    elif self.data_list[6] == "0c":
                        bit_info = "VBOX3 & Logging"
                    else:
                        bit_info = "Not specified"
                    return AnalyzerFrame('message_information', frame.start_time, frame.end_time, {
                            'info': 'VBOX information',
                            'input_type': bit_info,
                        })
                elif len(self.data_list) == 8:
                    val = bin(int(("0x" + self.data_list[7]), 16))
                    leading_zero = "0" * (10 - len(val))
                    bin_val = leading_zero + val[2:]
                    info = []
                    if bin_val[3] == "1":
                        info.append("Brake test started")
                    if bin_val[4] == "1":
                        info.append("Brake trigger active")
                    if bin_val[5] == "1":
                        info.append("DGPS Active")
                    if bin_val[6] == "1":
                        info.append("Dual Antenna Active")
                    if bin_val[3] == "0" and bin_val[4] == "0" and bin_val[5] == "0" and bin_val[6] == "0":
                        info.append("No additional information")
                    self.data_list = []
                    if ("Brake test started" in info or "Brake trigger active" in info) and self.first_301 == True and bin_val[-1] == "1":
                        start_to_end = frame.end_time - self.id301_start_time
                        start_to_trigger_difference = frame.end_time - self.last301
                        frame_time = str(start_to_end - start_to_trigger_difference)
                        new_time = frame_time.split(" ").pop(1)
                        time = float((new_time.split("millisecond=").pop(1))[:-1])
                        if time > 18:
                            self.delay_ms.append(float(time))
                            print(f"\nNumber of delays counted - {len(self.delay_ms)}")
                            print(f"Average delay - {sum(self.delay_ms) / len(self.delay_ms)}ms")
                            mode = most_common(self.delay_ms)
                            print(f"Anomalous data - {[x for x in self.delay_ms if mode - 1 >= x or x >= mode + 1] if len([x for x in self.delay_ms if mode - 1 >= x or x >= mode + 1]) is not 0 else None}")
                        self.first_301 = False
                    self.frame_start_time = []
                    self.frame_end_time = []
                    status_info = ", ".join(info)
                    return AnalyzerFrame('message_information', frame.start_time, frame.end_time, {
                            'info': 'Status information',
                            'input_type': status_info,
                        })
        # converts 304 into brake trigger distance, long acc, lat acc
            elif self.id == 772:
                if len(self.data_list) == 4:
                    hex_join = "".join(self.data_list[0:4])
                    converted_hex = int(hex_join, 16)
                    trigger_distance = converted_hex * 0.000078125 
                    return AnalyzerFrame('message_information', self.frame_start_time[0], self.frame_end_time[3], {
                            'info': 'Trigger Distance',
                            'input_type': str(round(trigger_distance, 3)) + "m",
                        })
                elif len(self.data_list) == 6:
                    hex_join = "".join(self.data_list[4:6])
                    converted_hex = int(hex_join, 16)
                    long_acc = converted_hex * 0.01
                    return AnalyzerFrame('message_information', self.frame_start_time[4], self.frame_end_time[5], {
                            'info': 'Longitudinal Acceleration',
                            'input_type': str(round(long_acc, 3)) + "g",
                        })
                elif len(self.data_list) == 8:
                    hex_join = "".join(self.data_list[6:])
                    converted_hex = int(hex_join, 16)
                    lat_acc = converted_hex * 0.01
                    last_start_time = self.frame_start_time[6]
                    last_end_time = self.frame_end_time[7]
                    self.data_list = []
                    self.frame_start_time = []
                    self.frame_end_time = []
                    return AnalyzerFrame('message_information', last_start_time, last_end_time, {
                            'info': 'Lateral Acceleration',
                            'input_type': str(round(lat_acc, 3)) + "g",
                        })
            # 305
            elif self.id == 773:
                if len(self.data_list) == 4:
                    hex_join = "".join(self.data_list[0:4])
                    converted_hex = int(hex_join, 16)
                    distance_travelled = converted_hex * 0.000078125 
                    return AnalyzerFrame('message_information', self.frame_start_time[0], self.frame_end_time[3], {
                            'info': 'Distance Travelled',
                            'input_type': str(round(distance_travelled, 3)) + "m",
                        })
                elif len(self.data_list) == 6:
                    hex_join = "".join(self.data_list[4:6])
                    converted_hex = int(hex_join, 16)
                    Trigger_Time = converted_hex * 0.01
                    return AnalyzerFrame('message_information', self.frame_start_time[4], self.frame_end_time[5], {
                            'info': 'Trigger Time',
                            'input_type': str(round(Trigger_Time, 3)),
                        })
                elif len(self.data_list) == 8:
                    hex_join = "".join(self.data_list[6:])
                    converted_hex = int(hex_join, 16)
                    trigger_speed = converted_hex * 0.01 * 1.852
                    last_start_time = self.frame_start_time[6]
                    last_end_time = self.frame_end_time[7]
                    self.data_list = []
                    self.frame_start_time = []
                    self.frame_end_time = []
                    return AnalyzerFrame('message_information', last_start_time, last_end_time, {
                            'info': 'Speed at trigger',
                            'input_type': str(round(trigger_speed, 3)) + "km/h",
                        })
            # converts 306
            elif self.id == 774:
                if len(self.data_list) == 2:
                    hex_join = "".join(self.data_list[0:2])
                    converted_hex = int(hex_join, 16)
                    speed_quality = converted_hex * 0.01
                    return AnalyzerFrame('message_information', self.frame_start_time[0], self.frame_end_time[1], {
                            'info': 'Speed Quality',
                            'input_type': str(round(speed_quality, 3)) + "km/h",
                        })
                elif len(self.data_list) == 4:
                    hex_join = "".join(self.data_list[2:4])
                    converted_hex = int(hex_join, 16)
                    true_heading = converted_hex * 0.01
                    return AnalyzerFrame('message_information', self.frame_start_time[2], self.frame_end_time[3], {
                            'info': 'True Heading',
                            'input_type': str(round(true_heading, 3)) + "°",
                        })
                elif len(self.data_list) == 6:
                    hex_join = "".join(self.data_list[4:6])
                    converted_hex = int(hex_join, 16)
                    slip_angle = converted_hex * 0.01
                    return AnalyzerFrame('message_information', self.frame_start_time[4], self.frame_end_time[5], {
                            'info': 'Slip Angle',
                            'input_type': str(round(slip_angle, 3)) + "°",
                        })
                elif len(self.data_list) == 8:
                    hex_join = "".join(self.data_list[6:])
                    converted_hex = int(hex_join, 16)
                    pitch_angle = converted_hex * 0.01
                    last_start_time = self.frame_start_time[6]
                    last_end_time = self.frame_end_time[7]
                    self.data_list = []
                    self.frame_start_time = []
                    self.frame_end_time = []
                    return AnalyzerFrame('message_information', last_start_time, last_end_time, {
                            'info': 'Slip Angle',
                            'input_type': str(round(pitch_angle, 3)) + "°",
                        })
            # 307
            elif self.id == 775:
                if len(self.data_list) == 2:
                    hex_join = "".join(self.data_list[0:2])
                    converted_hex = int(hex_join, 16)
                    lateral_velocity = converted_hex * 0.01
                    return AnalyzerFrame('message_information', self.frame_start_time[0], self.frame_end_time[1], {
                            'info': 'Lateral Velocity',
                            'input_type': str(round(lateral_velocity, 3)) + "km/h",
                        })
                elif len(self.data_list) == 4:
                    hex_join = "".join(self.data_list[2:4])
                    converted_hex = int(hex_join, 16)
                    yaw_rate = converted_hex * 0.01
                    return AnalyzerFrame('message_information', self.frame_start_time[2], self.frame_end_time[3], {
                            'info': 'Yaw Rate',
                            'input_type': str(round(yaw_rate, 3)) + "°/s",
                        })
                elif len(self.data_list) == 6:
                    hex_join = "".join(self.data_list[4:6])
                    converted_hex = int(hex_join, 16)
                    roll_angle = converted_hex * 0.01
                    return AnalyzerFrame('message_information', self.frame_start_time[4], self.frame_end_time[5], {
                            'info': 'Slip Angle',
                            'input_type': str(round(roll_angle, 3)) + "°",
                        })
                elif len(self.data_list) == 8:
                    hex_join = "".join(self.data_list[6:])
                    converted_hex = int(hex_join, 16)
                    longitudinal_velocity = converted_hex * 0.01
                    last_start_time = self.frame_start_time[6]
                    last_end_time = self.frame_end_time[7]
                    self.data_list = []
                    self.frame_start_time = []
                    self.frame_end_time = []
                    return AnalyzerFrame('message_information', last_start_time, last_end_time, {
                            'info': 'Longitudinal Velocity',
                            'input_type': str(round(longitudinal_velocity, 3)) + "km/h",
                        })
            # 308
            elif self.id == 776:
                if len(self.data_list) == 6:
                    hex_join = "".join(self.data_list[0:6])
                    converted_hex = int(hex_join, 16)
                    lat_48bit = converted_hex / 10000000 
                    return AnalyzerFrame('message_information', self.frame_start_time[0], self.frame_end_time[5], {
                            'info': 'Latitude 48bit',
                            'input_type': str(lat_48bit),
                        })
                elif len(self.data_list) == 7:
                    position_quality = int(self.data_list[6], 16)
                    return AnalyzerFrame('message_information', frame.start_time, frame.end_time, {
                            'info': 'Position Quality',
                            'input_type': str(position_quality),
                        })
                elif len(self.data_list) == 8:
                    converted_hex = int(self.data_list[7], 16)
                    if converted_hex == 0:
                        kf_status = "None"
                    elif converted_hex == 1:
                        kf_status = "GNSS Only"
                    elif converted_hex == 2:
                        kf_status = "DGPS"
                    elif converted_hex == 3:
                        kf_status = "RTK Float"
                    elif converted_hex == 4:
                        kf_status = "RTK Fixed"                    
                    elif converted_hex == 6:
                        kf_status = "IMU Coast"
                    else:
                        kf_status = "Not stated"
                    self.data_list = []
                    self.frame_start_time = []
                    self.frame_end_time = []
                    return AnalyzerFrame('message_information', frame.start_time, frame.end_time, {
                            'info': 'Kalman Filter Status',
                            'input_type': str(kf_status),
                        })
            # 309
            elif self.id == 777:
                if len(self.data_list) == 6:
                    hex_join = "".join(self.data_list[0:6])
                    converted_hex = int(hex_join, 16)
                    additional_hex = int('ffff00000000', 16)
                    long_48bit = (additional_hex - converted_hex) / 10000000
                    return AnalyzerFrame('message_information', self.frame_start_time[0], self.frame_end_time[5], {
                            'info': 'Longitude 48bit',
                            'input_type': str(long_48bit),
                        })
                elif len(self.data_list) == 8:
                    hex_join = "".join(self.data_list[6:])
                    converted_hex = int(hex_join, 16)
                    speed_robot_nav = converted_hex * 0.01 * 1.852
                    self.speed_robot.append(speed_robot_nav)
                    try: 
                        if ((speed - 0.01) <= speed or (speed + 0.01) >= speed) in self.speed_robot:
                            self.speed_robot.remove(speed)
                            print(f"Speed delay - {len(self.speed_robot)} samples")
                        elif speed > self.speed_robot[0]:
                            self.speed_robot.clear()
                    except:
                        pass
                    last_start_time = self.frame_start_time[6]
                    last_end_time = self.frame_end_time[7]
                    self.data_list = []
                    self.frame_start_time = []
                    self.frame_end_time = []
                    return AnalyzerFrame('message_information', last_start_time, last_end_time, {
                            'info': 'Speed Robot Nav',
                            'input_type': str(round(speed_robot_nav, 3)) + "km/h",
                        })
            elif self.id == 788:
                if len(self.data_list) == 2:
                    hex_join = "".join(self.data_list[0:2])
                    converted_hex = int(hex_join, 16)
                    slip_angle_COG = converted_hex * 0.01
                    return AnalyzerFrame('message_information', self.frame_start_time[0], self.frame_end_time[1], {
                            'info': 'Slip Angle COG',
                            'input_type': str(round(slip_angle_COG, 3)) + "°",
                        })
                elif len(self.data_list) == 3:
                    hex_join = "".join(self.data_list[0:2])
                    converted_hex = int(hex_join, 16)
                    sats_robot_nav = converted_hex
                    return AnalyzerFrame('message_information', frame.start_time, frame.end_time, {
                            'info': 'Sats Robot Nav',
                            'input_type': str(sats_robot_nav),
                        })
                elif len(self.data_list) == 6:
                    hex_join = "".join(self.data_list[3:6])
                    converted_hex = int(hex_join, 16)
                    tsm_robot_nav = datetime.timedelta(seconds=(int(converted_hex) * 0.01))
                    self.undelay_utc.append(tsm_robot_nav)
                    try:
                        if (UTCTime + datetime.timedelta(seconds=18)) in self.undelay_utc:
                            self.undelay_utc.remove((UTCTime + datetime.timedelta(seconds=18)))
                            if self.utc_count == len(self.undelay_utc):
                                print(f"Time since midnight delay - {len(self.undelay_utc)} samples")
                                self.utc_count = 1
                            else:
                                self.utc_count += 1
                        elif (UTCTime + datetime.timedelta(seconds=18)) > self.undelay_utc[0]:
                            self.undelay_utc.clear()
                    except:
                        pass
                    return AnalyzerFrame('message_information', self.frame_start_time[3], self.frame_end_time[5], {
                            'info': 'UTC robot nav',
                            'input_type': str(tsm_robot_nav),
                        })
                elif len(self.data_list) == 8:
                    hex_join = "".join(self.data_list[6:])
                    converted_hex = int(hex_join, 16)
                    robot_head_nav = converted_hex * 0.01
                    last_start_time = self.frame_start_time[6]
                    last_end_time = self.frame_end_time[7]
                    self.data_list = []
                    self.frame_start_time = []
                    self.frame_end_time = []
                    return AnalyzerFrame('message_information', last_start_time, last_end_time, {
                            'info': 'RobotHead',
                            'input_type': str(round(robot_head_nav, 3)) + "°",
                        })
            elif self.id == 809:
                if len(self.data_list) == 4:
                    hex_join = "".join(self.data_list[0:4])
                    packed = struct.unpack('>f', bytes.fromhex(hex_join))
                    x_pos = packed[0]
                    return AnalyzerFrame('message_information', self.frame_start_time[0], self.frame_end_time[3], {
                            'info': 'X position',
                            'input_type': str(round(x_pos, 9)) + "m",
                        })
                elif len(self.data_list) == 8:
                    hex_join = "".join(self.data_list[4:])
                    packed = struct.unpack('>f', bytes.fromhex(hex_join))
                    y_pos = packed[0]
                    last_start_time = self.frame_start_time[4]
                    last_end_time = self.frame_end_time[7]
                    self.data_list = []
                    self.frame_start_time = []
                    self.frame_end_time = []
                    return AnalyzerFrame('message_information', last_start_time, last_end_time, {
                            'info': 'Y position',
                            'input_type': str(round(y_pos, 9)) + "m",
                        })
            elif self.id == 810:
                if len(self.data_list) == 2:
                    hex_join = "".join(self.data_list[0:2])
                    converted_hex = int(hex_join, 16)
                    robothead_vehico = converted_hex * 0.01
                    return AnalyzerFrame('message_information', self.frame_start_time[0], self.frame_end_time[1], {
                            'info': 'RobotHead_Vehico',
                            'input_type': str(round(robothead_vehico, 3)) + "°",
                        })
                elif len(self.data_list) == 4:
                    hex_join = "".join(self.data_list[2:4])
                    converted_hex = int(hex_join, 16)
                    speed_vehico = converted_hex * 0.01
                    return AnalyzerFrame('message_information', self.frame_start_time[2], self.frame_end_time[3], {
                            'info': 'Speed_Vehico',
                            'input_type': str(round(speed_vehico, 3)) + "km/h",
                        })
                elif len(self.data_list) == 5:
                    hex_join = "".join(self.data_list[4])
                    converted_hex = int(hex_join, 16)
                    pos_qual_vehico = converted_hex
                    return AnalyzerFrame('message_information', frame.start_time, frame.end_time, {
                            'info': 'Position Quality Vehico',
                            'input_type': str(pos_qual_vehico),
                        })
                elif len(self.data_list) == 6:
                    hex_join = "".join(self.data_list[5])
                    converted_hex = int(hex_join, 16)
                    solution_type_vehico = converted_hex
                    return AnalyzerFrame('message_information', frame.start_time, frame.end_time, {
                            'info': 'Solution Type Vehico',
                            'input_type': str(solution_type_vehico),
                        })
                elif len(self.data_list) == 8:
                    hex_join = "".join(self.data_list[6:])
                    converted_hex = int(hex_join, 16)
                    last_start_time = self.frame_start_time[6]
                    last_end_time = self.frame_end_time[7]
                    self.data_list = []
                    self.frame_start_time = []
                    self.frame_end_time = []
                    return AnalyzerFrame('message_information', last_start_time, last_end_time, {
                            'info': 'N/A',
                            'input_type': str(converted_hex),
                        })
            else:
                self.id = None
                self.data_list = []
                self.frame_start_time = []
                self.frame_end_time = []
                return AnalyzerFrame('message_information', frame.start_time, frame.end_time, {
                    'error': 'Error!'
                })

