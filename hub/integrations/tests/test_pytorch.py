from hub.tests.common import assert_all_samples_have_expected_compression
from hub.constants import UNCOMPRESSED
from hub.api.dataset import Dataset
import numpy as np

from hub.integrations.pytorch_old import dataset_to_pytorch
from hub.util.check_installation import requires_torch


@requires_torch
def test_pytorch_with_compression(local_ds: Dataset):
    import torch

    # TODO: chunk-wise compression for labels (right now they are uncompressed)
    images = local_ds.create_tensor("images", htype="image")
    labels = local_ds.create_tensor("labels", htype="class_label")

    images.extend(np.ones((16, 100, 100, 3), dtype="uint8"))
    labels.extend(np.ones((16, 1), dtype="int32"))

    # make sure data is appropriately compressed
    assert images.meta.sample_compression == "png"
    assert labels.meta.sample_compression == UNCOMPRESSED
    assert_all_samples_have_expected_compression(images, ["png"] * 16)
    assert_all_samples_have_expected_compression(labels, [UNCOMPRESSED] * 16)

    ptds = local_ds.pytorch(workers=2)
    dl = torch.utils.data.DataLoader(ptds, batch_size=1, num_workers=0)

    for batch in dl:
        X = batch["images"].numpy()
        T = batch["labels"].numpy()
        assert X.shape == (1, 100, 100, 3)
        assert T.shape == (1, 1)


# TODO: this test is uncommented because of the "cannot have 2 pytorch datasets open" bug. i think it's due to global variables.
# TODO: should uncomment this once that works. for now the compression test tests both uncompressed and compressed data, but we
# TODO: should have these separate
# @requires_torch
# def test_pytorch_small(local_ds):
#     import torch
#
#     local_ds.create_tensor("image")
#
#     local_ds.image.extend(
#         np.array([i * np.ones((300, 300)) for i in range(256)], dtype="uint8")
#     )
#     local_ds.create_tensor("image2")
#     local_ds.image2.extend(np.array([i * np.ones((100, 100)) for i in range(256)]))
#     local_ds.flush()
#
#     ptds = local_ds.pytorch(workers=2)
#
#     # always use num_workers=0, when using hub workers
#     dl = torch.utils.data.DataLoader(
#         ptds,
#         batch_size=1,
#         num_workers=0,
#     )
#     for i, batch in enumerate(dl):
#         np.testing.assert_array_equal(
#             batch["image"].numpy(), i * np.ones((1, 300, 300))
#         )
#         np.testing.assert_array_equal(
#             batch["image2"].numpy(), i * np.ones((1, 100, 100))
#         )
#     local_ds.delete()


@requires_torch
def test_pytorch_small_old(local_ds):
    import torch

    local_ds.create_tensor("image")
    local_ds.image.extend(np.array([i * np.ones((300, 300)) for i in range(256)]))
    local_ds.create_tensor("image2")
    local_ds.image2.extend(np.array([i * np.ones((100, 100)) for i in range(256)]))
    local_ds.flush()

    # .pytorch will automatically switch depending on version, this syntax is being used to ensure testing of old code on Python 3.8
    ptds = dataset_to_pytorch(local_ds, workers=2, python_version_warning=False)
    dl = torch.utils.data.DataLoader(
        ptds,
        batch_size=1,
        num_workers=0,
    )
    for i, batch in enumerate(dl):
        np.testing.assert_array_equal(
            batch["image"].numpy(), i * np.ones((1, 300, 300))
        )
        np.testing.assert_array_equal(
            batch["image2"].numpy(), i * np.ones((1, 100, 100))
        )
    local_ds.delete()


@requires_torch
def test_pytorch_large_old(local_ds):
    import torch

    # don't need to test with compression because it uses the API (which is tested for iteration + compression)
    local_ds.create_tensor("image")

    arr = np.array(
        [
            np.ones((4096, 4096)),
            2 * np.ones((4096, 4096)),
            3 * np.ones((4096, 4096)),
            4 * np.ones((4096, 4096)),
        ],
        dtype="uint8",
    )
    local_ds.image.extend(arr)
    local_ds.create_tensor("classlabel")
    local_ds.classlabel.extend(np.array([i for i in range(10)], dtype="uint32"))
    local_ds.flush()

    # .pytorch will automatically switch depending on version, this syntax is being used to ensure testing of old code on Python 3.8
    ptds = dataset_to_pytorch(local_ds, workers=2, python_version_warning=False)
    dl = torch.utils.data.DataLoader(
        ptds,
        batch_size=1,
        num_workers=0,
    )
    for i, batch in enumerate(dl):
        actual_image = batch["image"].numpy()
        expected_image = (i + 1) * np.ones((1, 4096, 4096))

        actual_label = batch["classlabel"].numpy()
        expected_label = (i) * np.ones((1,))

        np.testing.assert_array_equal(actual_image, expected_image)
        np.testing.assert_array_equal(actual_label, expected_label)

    local_ds.delete()