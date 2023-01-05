# High Level Analyzer
# For more information and documentation, please go to https://support.saleae.com/extensions/high-level-analyzer-extensions

from saleae.analyzers import HighLevelAnalyzer, AnalyzerFrame, StringSetting, NumberSetting, ChoicesSetting
from saleae.data import GraphTimeDelta


# High level analyzers must subclass the HighLevelAnalyzer class.
class Hla(HighLevelAnalyzer):
    result_types = {
        'found': {
            'format': 'Data'
        },
    }

    def __init__(self):
        pass
   
    def decode(self, frame: AnalyzerFrame):
        if frame.type == "identifier_field":
            return AnalyzerFrame('found', frame.start_time, frame.end_time, {})