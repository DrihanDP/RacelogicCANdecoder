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
        # if frame.type == "data_field":
        #     if self.id == 769:
        #         data_num += 1
        #         message_data = frame.data["data"][0]
        #         if data_num == 1:
        #             return AnalyzerFrame('message_information', frame.start_time, frame.end_time, {
        #                 'info': 'Sats',
        #                 'input_type': message_data,
        #             })


        # # start of the CAN message
        # if frame.type == "identifier_field":
        #     self.id = frame.data['identifier']
        #     self.temp_frame = AnalyzerFrame("message_information", frame.start_time, frame.end_time, {
        #         'info': 'ID',
        #         'input_type': hex(self.id),
        #     })

        # Actual data conversion
        if frame.type == "data_field" and self.id == 769:
            data_byte = hex(frame.data["data"][0])
            data_byte = data_byte[2:]
            if len(data_byte) == 1:
                new_data_byte = "0" + data_byte
                data_list.append(new_data_byte)
            else:
                data_list.append(data_byte)
            frame_start_time.append(frame.start_time)
            frame_end_time.append(frame.end_time)
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

        # elif frame.type == "data_field" and self.id == 770:
        #     data_byte = hex(frame.data["data"][0])
        #     data_byte = data_byte[2:]
        #     if len(data_byte) == 1:
        #         new_data_byte = "0" + data_byte
        #         data_list.append(new_data_byte)
        #     else:
        #         data_list.append(data_byte)
        #     frame_start_time.append(frame.start_time)
        #     frame_end_time.append(frame.end_time)
        #     if len(data_list) == 4:
        #         hex_join = "".join(data_list[:4])
        #         converted_hex = int(hex_join, 16)
        #         long = converted_hex / 100000
        #         return AnalyzerFrame('message_information', frame_start_time[0], frame_end_time[3], {
        #                 'info': 'Longitude',
        #                 'input_type': long,
        #             })
        #     if len(data_list) == 6:
        #         hex_join = "".join(data_list[4:6])
        #         converted_hex = int(hex_join, 16)
        #         speed = converted_hex * 0.01 * 1.852 # convert knots to km/h
        #         return AnalyzerFrame('message_information', frame_start_time[0], frame_end_time[3], {
        #                 'info': 'Speed',
        #                 'input_type': str(speed) + "km/h",
        #             })
                
        # end of CAN message
        # if frame.type == "crc_field":
        #     self.temp_frame.end_time = frame.end_time
        #     new_frame = self.temp_frame
        #     self.temp_frame = None
        #     return new_frame
