# High Level Analyzer
# For more information and documentation, please go to https://support.saleae.com/extensions/high-level-analyzer-extensions

from saleae.analyzers import HighLevelAnalyzer, AnalyzerFrame, StringSetting, NumberSetting, ChoicesSetting
from saleae.data import GraphTimeDelta
import datetime


data_list = []
frame_start_time = []
frame_end_time = []
# High level analyzers must subclass the HighLevelAnalyzer class.
class Hla(HighLevelAnalyzer):
    temp_frame = None
    result_types = {
        'message_information': {
            'format': 'Info: {{data.info}}, Value: {{data.input_type}}',
        },
        'error': {
            'format': 'Error!'
        }
    }

    def __init__(self):
        pass

    def decode(self, frame: AnalyzerFrame):
        global data_list, frame_start_time, frame_end_time
        if frame.type == 'identifier_field':
            self.id = frame.data['identifier']
            return AnalyzerFrame('message_information', frame.start_time, frame.end_time, {
                'info': 'ID',
                'input_type': hex(self.id),
            })
        # Actual data conversion
        if frame.type == "can_error":
            print("error frame")
            self.id = None
            data_list = []
            frame_start_time = []
            frame_end_time = []
            return AnalyzerFrame('message_information', frame.start_time, frame.end_time, {
                'error': 'Error!'
                })
        elif frame.type == "data_field":
            data_byte = hex(frame.data["data"][0])
            data_byte = data_byte[2:]
            if len(data_byte) == 1:
                new_data_byte = "0" + data_byte
                data_list.append(new_data_byte)
            else:
                data_list.append(data_byte)
            frame_start_time.append(frame.start_time)
            frame_end_time.append(frame.end_time)
            # 301
            if self.id == 769:
                if len(data_list) == 1:
                    return AnalyzerFrame('message_information', frame.start_time, frame.end_time, {
                            'info': 'Sats',
                            'input_type': int(data_list[0], 16),
                        })
                elif len(data_list) == 4:
                    hex_join = "".join(data_list[1:4])
                    converted_hex = int(hex_join, 16)
                    UTCTime = datetime.timedelta(seconds=(int(converted_hex) * 0.01))
                    return AnalyzerFrame('message_information', frame_start_time[1], frame_end_time[3], {
                            'info': 'UTC',
                            'input_type': str(UTCTime),
                        })
                elif len(data_list) == 8:
                    hex_join = "".join(data_list[4:])
                    converted_hex = int(hex_join, 16)
                    lat = converted_hex / 100000
                    last_start_time = frame_start_time[4]
                    last_end_time = frame_end_time[7]
                    data_list = []
                    frame_start_time = []
                    frame_end_time = []
                    return AnalyzerFrame('message_information', last_start_time, last_end_time, {
                            'info': 'Latitude',
                            'input_type': lat,
                        })
        # Converts 302 into longitude, speed, heading
            elif self.id == 770:
                if len(data_list) == 4:
                    hex_join = "".join(data_list[:4])
                    converted_hex = int(hex_join, 16)
                    long = converted_hex / 100000
                    return AnalyzerFrame('message_information', frame_start_time[0], frame_end_time[3], {
                            'info': 'Longitude',
                            'input_type': long,
                        })
                elif len(data_list) == 6:
                    hex_join = "".join(data_list[4:6])
                    converted_hex = int(hex_join, 16)
                    speed = converted_hex * 0.01 * 1.852 # convert knots to km/h
                    return AnalyzerFrame('message_information', frame_start_time[4], frame_end_time[5], {
                            'info': 'Speed',
                            'input_type': str(round(speed, 3)) + "km/h",
                        })
                elif len(data_list) == 8:
                    hex_join = "".join(data_list[6:])
                    converted_hex = int(hex_join, 16)
                    heading = converted_hex * 0.01
                    last_start_time = frame_start_time[6]
                    last_end_time = frame_end_time[7]
                    data_list = []
                    frame_start_time = []
                    frame_end_time = []
                    return AnalyzerFrame('message_information', last_start_time, last_end_time, {
                            'info': 'Heading',
                            'input_type': str(round(heading, 3)) + "°"
                        })
        # converts 303 into altitude, vertical velocity, addition info, status info
            elif self.id == 771:
                if len(data_list) == 3:
                    hex_join = "".join(data_list[:3])
                    converted_hex = int(hex_join, 16)
                    altitude = converted_hex * 0.01
                    return AnalyzerFrame('message_information', frame_start_time[0], frame_end_time[2], {
                            'info': 'Altitude',
                            'input_type': str(round(altitude, 3)) + "m",
                        })
                elif len(data_list) == 5:
                    hex_join = "".join(data_list[3:5])
                    converted_hex = int(hex_join, 16)
                    vertical_velocity = converted_hex * 0.01
                    return AnalyzerFrame('message_information', frame_start_time[3], frame_end_time[4], {
                            'info': 'Vertical Velocity',
                            'input_type': str(round(vertical_velocity, 3)) + "m/s",
                        })
                elif len(data_list) == 6:
                    return AnalyzerFrame('message_information', frame.start_time, frame.end_time, {
                            'info': 'Unused',
                            'input_type': 'N/A',
                        })
                elif len(data_list) == 7:
                    if data_list[6] == "04":
                        bit_info = "VBOX3"
                    elif data_list[6] == "08":
                        bit_info = "logging"
                    elif data_list[6] == "0c":
                        bit_info = "VBOX3 & Logging"
                    else:
                        bit_info = "Not specified"
                    return AnalyzerFrame('message_information', frame.start_time, frame.end_time, {
                            'info': 'VBOX information',
                            'input_type': bit_info,
                        })
                elif len(data_list) == 8:
                    if data_list[7] == "01":
                        status_info = "No additional information"
                    elif data_list[7] == "05":
                        status_info = "Brake test started"
                    elif data_list[7] == "09":
                        status_info = "Brake Trigger active"
                    elif data_list[7] == "11":
                        status_info = "DGPS active"
                    elif data_list[7] == "21":
                        status_info = "Dual lock"
                    else:
                        status_info = "Not stated"
                    data_list = []
                    frame_start_time = []
                    frame_end_time = []
                    return AnalyzerFrame('message_information', frame.start_time, frame.end_time, {
                            'info': 'Status information',
                            'input_type': status_info,
                        })
        # converts 304 into brake trigger distance, long acc, lat acc
            elif self.id == 772:
                if len(data_list) == 4:
                    hex_join = "".join(data_list[0:4])
                    converted_hex = int(hex_join, 16)
                    trigger_distance = converted_hex * 0.000078125 
                    return AnalyzerFrame('message_information', frame_start_time[0], frame_end_time[3], {
                            'info': 'Trigger Distance',
                            'input_type': str(round(trigger_distance, 3)) + "m",
                        })
                elif len(data_list) == 6:
                    hex_join = "".join(data_list[4:6])
                    converted_hex = int(hex_join, 16)
                    long_acc = converted_hex * 0.01
                    return AnalyzerFrame('message_information', frame_start_time[4], frame_end_time[5], {
                            'info': 'Longitudinal Acceleration',
                            'input_type': str(round(long_acc, 3)) + "g",
                        })
                elif len(data_list) == 8:
                    hex_join = "".join(data_list[6:])
                    converted_hex = int(hex_join, 16)
                    lat_acc = converted_hex * 0.01
                    last_start_time = frame_start_time[6]
                    last_end_time = frame_end_time[7]
                    data_list = []
                    frame_start_time = []
                    frame_end_time = []
                    return AnalyzerFrame('message_information', last_start_time, last_end_time, {
                            'info': 'Lateral Acceleration',
                            'input_type': str(round(lat_acc, 3)) + "g",
                        })
            # 305
            elif self.id == 773:
                if len(data_list) == 4:
                    hex_join = "".join(data_list[0:4])
                    converted_hex = int(hex_join, 16)
                    distance_travelled = converted_hex * 0.000078125 
                    return AnalyzerFrame('message_information', frame_start_time[0], frame_end_time[3], {
                            'info': 'Distance Travelled',
                            'input_type': str(round(distance_travelled, 3)) + "m",
                        })
                elif len(data_list) == 6:
                    hex_join = "".join(data_list[4:6])
                    converted_hex = int(hex_join, 16)
                    Trigger_Time = converted_hex * 0.01
                    return AnalyzerFrame('message_information', frame_start_time[4], frame_end_time[5], {
                            'info': 'Trigger Time',
                            'input_type': str(round(Trigger_Time, 3)),
                        })
                elif len(data_list) == 8:
                    hex_join = "".join(data_list[6:])
                    converted_hex = int(hex_join, 16)
                    trigger_speed = converted_hex * 0.01 * 1.852
                    last_start_time = frame_start_time[6]
                    last_end_time = frame_end_time[7]
                    data_list = []
                    frame_start_time = []
                    frame_end_time = []
                    return AnalyzerFrame('message_information', last_start_time, last_end_time, {
                            'info': 'Speed at trigger',
                            'input_type': str(round(trigger_speed, 3)) + "km/h",
                        })
            # converts 306
            elif self.id == 774:
                if len(data_list) == 2:
                    hex_join = "".join(data_list[0:2])
                    converted_hex = int(hex_join, 16)
                    speed_quality = converted_hex * 0.01
                    return AnalyzerFrame('message_information', frame_start_time[0], frame_end_time[1], {
                            'info': 'Speed Quality',
                            'input_type': str(round(speed_quality, 3)) + "km/h",
                        })
                elif len(data_list) == 4:
                    hex_join = "".join(data_list[2:4])
                    converted_hex = int(hex_join, 16)
                    true_heading = converted_hex * 0.01
                    return AnalyzerFrame('message_information', frame_start_time[2], frame_end_time[3], {
                            'info': 'True Heading',
                            'input_type': str(round(true_heading, 3)) + "°",
                        })
                elif len(data_list) == 6:
                    hex_join = "".join(data_list[4:6])
                    converted_hex = int(hex_join, 16)
                    slip_angle = converted_hex * 0.01
                    return AnalyzerFrame('message_information', frame_start_time[4], frame_end_time[5], {
                            'info': 'Slip Angle',
                            'input_type': str(round(slip_angle, 3)) + "°",
                        })
                elif len(data_list) == 8:
                    hex_join = "".join(data_list[6:])
                    converted_hex = int(hex_join, 16)
                    pitch_angle = converted_hex * 0.01
                    last_start_time = frame_start_time[6]
                    last_end_time = frame_end_time[7]
                    data_list = []
                    frame_start_time = []
                    frame_end_time = []
                    return AnalyzerFrame('message_information', last_start_time, last_end_time, {
                            'info': 'Slip Angle',
                            'input_type': str(round(pitch_angle, 3)) + "°",
                        })
            # 307
            elif self.id == 775:
                if len(data_list) == 2:
                    hex_join = "".join(data_list[0:2])
                    converted_hex = int(hex_join, 16)
                    lateral_velocity = converted_hex * 0.01
                    return AnalyzerFrame('message_information', frame_start_time[0], frame_end_time[1], {
                            'info': 'Lateral Velocity',
                            'input_type': str(round(lateral_velocity, 3)) + "km/h",
                        })
                elif len(data_list) == 4:
                    hex_join = "".join(data_list[2:4])
                    converted_hex = int(hex_join, 16)
                    yaw_rate = converted_hex * 0.01
                    return AnalyzerFrame('message_information', frame_start_time[2], frame_end_time[3], {
                            'info': 'Yaw Rate',
                            'input_type': str(round(yaw_rate, 3)) + "°/s",
                        })
                elif len(data_list) == 6:
                    hex_join = "".join(data_list[4:6])
                    converted_hex = int(hex_join, 16)
                    roll_angle = converted_hex * 0.01
                    return AnalyzerFrame('message_information', frame_start_time[4], frame_end_time[5], {
                            'info': 'Slip Angle',
                            'input_type': str(round(roll_angle, 3)) + "°",
                        })
                elif len(data_list) == 8:
                    hex_join = "".join(data_list[6:])
                    converted_hex = int(hex_join, 16)
                    longitudinal_velocity = converted_hex * 0.01
                    last_start_time = frame_start_time[6]
                    last_end_time = frame_end_time[7]
                    data_list = []
                    frame_start_time = []
                    frame_end_time = []
                    return AnalyzerFrame('message_information', last_start_time, last_end_time, {
                            'info': 'Longitudinal Velocity',
                            'input_type': str(round(longitudinal_velocity, 3)) + "km/h",
                        })
            # 308
            elif self.id == 776:
                if len(data_list) == 6:
                    hex_join = "".join(data_list[0:6])
                    converted_hex = int(hex_join, 16)
                    lat_48bit = converted_hex / 10000000 
                    return AnalyzerFrame('message_information', frame_start_time[0], frame_end_time[5], {
                            'info': 'Latitude 48bit',
                            'input_type': str(lat_48bit),
                        })
                elif len(data_list) == 7:
                    position_quality = int(data_list[6], 16)
                    return AnalyzerFrame('message_information', frame.start_time, frame.end_time, {
                            'info': 'Position Quality',
                            'input_type': str(position_quality),
                        })
                elif len(data_list) == 8:
                    converted_hex = int(data_list[7], 16)
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
                    data_list = []
                    frame_start_time = []
                    frame_end_time = []
                    return AnalyzerFrame('message_information', frame.start_time, frame.end_time, {
                            'info': 'Kalman Filter Status',
                            'input_type': str(kf_status),
                        })
            # 309
            elif self.id == 777:
                if len(data_list) == 6:
                    hex_join = "".join(data_list[0:6])
                    converted_hex = int(hex_join, 16)
                    long_48bit = converted_hex / 10000000 
                    return AnalyzerFrame('message_information', frame_start_time[0], frame_end_time[5], {
                            'info': 'Longitude 48bit',
                            'input_type': str(long_48bit),
                        })
                elif len(data_list) == 8:
                    hex_join = "".join(data_list[6:])
                    converted_hex = int(hex_join, 16)
                    speed_robot_nav = converted_hex * 0.01 * 1.852
                    last_start_time = frame_start_time[6]
                    last_end_time = frame_end_time[7]
                    data_list = []
                    frame_start_time = []
                    frame_end_time = []
                    return AnalyzerFrame('message_information', last_start_time, last_end_time, {
                            'info': 'Speed Robot Nav',
                            'input_type': str(round(speed_robot_nav, 3)) + "km/h",
                        })
            else:
                self.id = None
                data_list = []
                frame_start_time = []
                frame_end_time = []
                print(self.id, data_list, frame_start_time, frame_end_time)
                return AnalyzerFrame('message_information', frame.start_time, frame.end_time, {
                    'error': 'Error!'
                })