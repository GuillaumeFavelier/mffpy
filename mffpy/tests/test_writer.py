"""
Copyright 2019 Brain Electrophysiology Laboratory Company LLC

Licensed under the ApacheLicense, Version 2.0(the "License");
you may not use this module except in compliance with the License.
You may obtain a copy of the License at:

http: // www.apache.org / licenses / LICENSE - 2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an
"AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
ANY KIND, either express or implied.
"""
from datetime import datetime
from os import makedirs, rmdir, remove
from os.path import join

import pytest
import numpy as np

from ..writer import Writer
from ..bin_writer import BinWriter
from ..reader import Reader
from ..xml_files import XML


def test_writer_receives_bad_init_data():
    """Test bin writer fails when initialized with non-int sampling rate"""
    BinWriter(100)
    with pytest.raises(AssertionError):
        BinWriter(100.0)


def test_writer_doesnt_overwrite():
    dirname = 'testdir.mff'
    makedirs(dirname)
    with pytest.raises(AssertionError):
        Writer(dirname)
    rmdir(dirname)


def test_writer_writes():
    dirname = 'testdir2.mff'
    # create some data and add it to a binary writer
    device = 'HydroCel GSN 256 1.0'
    num_samples = 10
    num_channels = 256
    sampling_rate = 128
    b = BinWriter(sampling_rate=sampling_rate, data_type='EEG')
    data = np.random.randn(num_channels, num_samples).astype(np.float32)
    b.add_block(data)
    # create an mffpy.Writer and add a file info, and the binary file
    W = Writer(dirname)
    startdatetime = datetime.strptime(
        '1984-02-18T14:00:10.000000+0100', XML._time_format)
    W.addxml('fileInfo', recordTime=startdatetime)
    W.add_coordinates_and_sensor_layout(device)
    W.addbin(b)
    W.write()
    # read it again; compare the result
    R = Reader(dirname)
    assert R.startdatetime == startdatetime
    # Read binary data and compare
    read_data = R.get_physical_samples_from_epoch(R.epochs[0])
    assert 'EEG' in read_data
    read_data, t0 = read_data['EEG']
    assert t0 == 0.0
    assert read_data == pytest.approx(data)
    layout = R.directory.filepointer('sensorLayout')
    layout = XML.from_file(layout)
    assert layout.name == device
    # cleanup
    try:
        remove(join(dirname, 'info.xml'))
        remove(join(dirname, 'info1.xml'))
        remove(join(dirname, 'epochs.xml'))
        remove(join(dirname, 'signal1.bin'))
        remove(join(dirname, 'coordinates.xml'))
        remove(join(dirname, 'sensorLayout.xml'))
        rmdir(dirname)
    except BaseException:
        raise AssertionError(f"""
        Clean-up failed of '{dirname}'.  Were additional files written?""")