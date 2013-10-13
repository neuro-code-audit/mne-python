import numpy as np
import os.path as op
from numpy.testing import assert_array_almost_equal
from nose.tools import assert_true

from mne import fiff
from mne import Epochs
from mne import read_events
from mne.time_frequency import compute_raw_psd, compute_epochs_psd
from mne.datasets import sample

raw_fname = op.join(op.dirname(__file__), '..', '..', 'fiff', 'tests', 'data',
                    'test_raw.fif')
data_path = sample.data_path()
event_fname = data_path + '/MEG/sample/sample_audvis_raw-eve.fif'

# Setup for reading the raw data
events = read_events(event_fname)


def test_psd():
    """Test PSD estimation
    """
    raw = fiff.Raw(raw_fname)

    exclude = raw.info['bads'] + ['MEG 2443', 'EEG 053']  # bads + 2 more

    # picks MEG gradiometers
    picks = fiff.pick_types(raw.info, meg='mag', eeg=False, stim=False,
                            exclude=exclude)

    picks = picks[:2]

    tmin, tmax = 0, 10  # use the first 60s of data
    fmin, fmax = 2, 70  # look at frequencies between 5 and 70Hz
    NFFT = 124  # the FFT size (NFFT). Ideally a power of 2
    psds, freqs = compute_raw_psd(raw, tmin=tmin, tmax=tmax, picks=picks,
                                  fmin=fmin, fmax=fmax, NFFT=NFFT, n_jobs=1,
                                  proj=False)
    psds_proj, freqs = compute_raw_psd(raw, tmin=tmin, tmax=tmax, picks=picks,
                                       fmin=fmin, fmax=fmax, NFFT=NFFT,
                                       n_jobs=1, proj=True)

    assert_array_almost_equal(psds, psds_proj)
    assert_true(psds.shape == (len(picks), len(freqs)))
    assert_true(np.sum(freqs < 0) == 0)
    assert_true(np.sum(psds < 0) == 0)



def test_psd_epochs():
    """Test PSD estimation on epochs
    """
    raw = fiff.Raw(raw_fname)

    exclude = raw.info['bads'] + ['MEG 2443', 'EEG 053']  # bads + 2 more

    # picks MEG gradiometers
    picks = fiff.pick_types(raw.info, meg='mag', eeg=False, stim=False,
                            exclude=exclude)

    picks = picks[:2]

    NFFT = 124  # the FFT size (NFFT). Ideally a power of 2

    tmin, tmax, event_id = -1, 1, 1
    include = []
    raw.info['bads'] += ['MEG 2443']  # bads

    # picks MEG gradiometers
    picks = fiff.pick_types(raw.info, meg='grad', eeg=False, eog=True,
                            stim=False, include=include, exclude='bads')

    epochs = Epochs(raw, events, event_id, tmin, tmax, picks=picks,
                    baseline=(None, 0),
                    reject=dict(grad=4000e-13, eog=150e-6), proj=False)

    NFFT = 256  # the FFT size (NFFT). Ideally a power of 2
    picks = fiff.pick_types(epochs.info, meg='grad', eeg=False, eog=True,
                            stim=False, include=include, exclude='bads')
    psds, freqs = compute_epochs_psd(epochs, fmin=2, fmax=300, NFFT=NFFT, picks=picks,
                                     n_jobs=1).next()
    psds_proj, _ = compute_epochs_psd(epochs, fmin=2, fmax=300, NFFT=NFFT, n_jobs=1,
                                      picks=picks, proj=True).next()

    assert_array_almost_equal(psds, psds_proj)
    assert_true(psds.shape == (len(picks), len(freqs)))
    assert_true(np.sum(freqs < 0) == 0)
    assert_true(np.sum(psds < 0) == 0)
