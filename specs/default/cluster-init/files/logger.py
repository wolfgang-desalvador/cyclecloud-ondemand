import logging

from constants import LOGGING_PATH

logging.basicConfig(filename=LOGGING_PATH,
                        level=logging.DEBUG,
                        format='%(asctime)s: '    
                                '%(levelname)s: '
                                '%(message)s')

OnDemandCycleCloudLogger = logging.getLogger()
