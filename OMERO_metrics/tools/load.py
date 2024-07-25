import logging
from microscopemetrics_schema.datamodel.microscopemetrics_schema import (
    FieldIlluminationDataset,
    PSFBeadsDataset,
)
import yaml
import numpy as np
from omero.gateway import (
    BlitzGateway,
    DatasetWrapper,
    ImageWrapper,
    ProjectWrapper,
    FileAnnotationWrapper,
    MapAnnotationWrapper,
)
import microscopemetrics_schema.datamodel as mm_schema
from linkml_runtime.loaders import yaml_loader
import pandas as pd
from . import omero_tools
from .data_preperation import (
    get_table_originalFile_id,
    get_info_roi_lines,
    get_info_roi_rectangles,
    get_info_roi_points,
    get_rois_omero,
    add_colors_intensity_profile,
)

# Creating logging services
logger = logging.getLogger(__name__)
import collections
import omero

DATASET_TYPES = ["FieldIlluminationDataset", "PSFBeadsDataset"]

INPUT_IMAGES_MAPPING = {
    "FieldIlluminationDataset": "field_illumination_image",
    "PSFBeadsDataset": "psf_beads_images",
}

OUTPUT_DATA = {
    "FieldIlluminationDataset": "intensity_profiles",
    "PSFBeadsDataset": "psf_beads",
}

DATASET_IMAGES = {
    "FieldIlluminationDataset": {
        "input": ["field_illumination_image"],
        "output": [],
    },
    "PSFBeadsDataset": {
        "input": ["psf_beads_images"],
        "output": ["average_bead"],
    },
}


def image_exist(image_id, mm_dataset):
    image_found = False
    image_location = None
    index = None
    for k, v in DATASET_IMAGES[mm_dataset.__class__.__name__].items():
        if v:
            images_list = getattr(mm_dataset[k], v[0])
            if not isinstance(images_list, list):
                images_list = [images_list]
            for i, image in enumerate(images_list):
                if image_id == image.data_reference.omero_object_id:
                    image_found = True
                    image_location = k
                    index = i
                    break
    return image_found, image_location, index


def load_config_file_data(conn, project):
    exist = False
    for ann in project.listAnnotations():
        if isinstance(ann, FileAnnotationWrapper):
            ns = ann.getFile().getName()
            if ns.startswith("study_config.yaml"):
                exist = True
                setup = yaml.load(
                    ann.getFileInChunks().__next__().decode(),
                    Loader=yaml.SafeLoader,
                )
    if exist:
        return setup
    else:
        return None


def load_project(
    conn: BlitzGateway, project_id: int
) -> mm_schema.MetricsDatasetCollection:
    collection = mm_schema.MetricsDatasetCollection()
    file_anns = []
    dataset_types = []
    project = conn.getObject("Project", project_id)
    try:
        for file_ann in project.listAnnotations():
            if isinstance(file_ann, FileAnnotationWrapper):

                ds_type = file_ann.getFileName().split("_")[0]
                if ds_type in DATASET_TYPES:
                    file_anns.append(file_ann)
                    dataset_types.append(ds_type)

        for file_ann, ds_type in zip(file_anns, dataset_types):
            collection.datasets.append(
                yaml_loader.loads(
                    file_ann.getFileInChunks().__next__().decode(),
                    target_class=getattr(mm_schema, ds_type),
                )
            )
        return collection
    except Exception as e:
        logger.error(f"Error loading project {project_id}: {e}")
        return collection


def load_dataset(
    dataset: DatasetWrapper, load_images: bool = True
) -> mm_schema.MetricsDataset:
    mm_datasets = []
    for ann in dataset.listAnnotations():
        if isinstance(ann, FileAnnotationWrapper):
            ns = ann.getNs()
            if ns.startswith("microscopemetrics_schema:samples"):
                ds_type = ns.split("/")[-1]
                if ds_type in DATASET_TYPES:
                    mm_datasets.append(
                        yaml_loader.loads(
                            ann.getFileInChunks().__next__().decode(),
                            target_class=getattr(mm_schema, ds_type),
                        )
                    )
    if len(mm_datasets) == 1:
        mm_dataset = mm_datasets[0]
    elif len(mm_datasets) > 1:
        logger.warning(
            f"More than one dataset"
            f"found in dataset {dataset.getId()}."
            f"Using the first one"
        )
        mm_dataset = mm_datasets[0]
    else:
        logger.info(f"No dataset found in dataset {dataset.getId()}")
        return None

    if load_images:
        # First time loading the images the
        # dataset does not know which images to load
        if mm_dataset.processed:
            input_images = getattr(
                mm_dataset.input,
                INPUT_IMAGES_MAPPING[mm_dataset.__class__.__name__],
            )
            for input_image in input_images:
                image_wrapper = omero_tools.get_omero_obj_from_mm_obj(
                    dataset._conn, input_image
                )
                input_image.array_data = _load_image_intensities(image_wrapper)
        else:
            input_images = [
                load_image(image) for image in dataset.listChildren()
            ]
            setattr(
                mm_dataset,
                INPUT_IMAGES_MAPPING[mm_dataset.__class__.__name__],
                input_images,
            )
    else:
        setattr(
            mm_dataset, INPUT_IMAGES_MAPPING[mm_dataset.__class__.__name__], []
        )

    return mm_dataset


def load_dash_data_image(
    conn: BlitzGateway,
    mm_dataset: mm_schema.MetricsDataset,
    image: mm_schema.Image,
    image_index: int,
    image_location: str,
) -> dict:
    dash_context = {}
    if (
        isinstance(mm_dataset, FieldIlluminationDataset)
        and image_location == "input"
    ):
        dash_context["image"] = image.array_data
        dash_context["channel_names"] = image.channel_series
        ann_id = mm_dataset.output.__dict__["intensity_profiles"][
            image_index
        ].data_reference.omero_object_id
        roi_service = conn.getRoiService()
        result = roi_service.findByImage(
            int(image.data_reference.omero_object_id), None, conn.SERVICE_OPTS
        )
        shapes_rectangle, shapes_line, shapes_point = get_rois_omero(result)
        df_lines_omero = get_info_roi_lines(shapes_line)
        df_rects_omero = get_info_roi_rectangles(shapes_rectangle)
        df_points_omero = get_info_roi_points(shapes_point)
        dash_context["df_lines"] = df_lines_omero
        dash_context["df_rects"] = df_rects_omero
        dash_context["df_points"] = df_points_omero
        dash_context["df_intensity_profiles"] = get_table_file_id(conn, ann_id)
    elif (
        isinstance(mm_dataset, FieldIlluminationDataset)
        and image_location == "output"
    ):
        dash_context["image"] = image.array_data
        dash_context["channel_names"] = image.channel_series
        dash_context["message"] = (
            "No visualization available for output images."
        )
    elif isinstance(mm_dataset, PSFBeadsDataset) and image_location == "input":
        dash_context["image"] = image.array_data
        dash_context["min_distance"] = (
            mm_dataset.input.min_lateral_distance_factor
        )
        dash_context["channel_names"] = image.channel_series
        dash_context["bead_properties_df"] = get_table_file_id(
            conn,
            mm_dataset.output.bead_properties.data_reference.omero_object_id,
        )
    elif (
        isinstance(mm_dataset, PSFBeadsDataset) and image_location == "output"
    ):
        dash_context["image"] = image.array_data
        dash_context["channel_names"] = image.channel_series
        dash_context["message"] = (
            "No visualization available for output images."
        )

    else:
        dash_context = {}
    return dash_context


def load_dash_data_dataset(
    conn: BlitzGateway,
    dataset: mm_schema.MetricsDataset,
) -> dict:
    dash_context = {}
    if isinstance(dataset, FieldIlluminationDataset):
        title = "Field Illumination Dataset"
        dash_context["title"] = title
        df = get_images_intensity_profiles(dataset)
        dash_context["image"], channel_series = concatenate_images(
            dataset.input.field_illumination_image
        )
        dash_context["channel_names"] = channel_series
        dash_context["intensity_profiles"] = get_all_intensity_profiles(
            conn, df
        )
        dash_context["key_values_df"] = get_key_values(dataset.output)
    elif isinstance(dataset, PSFBeadsDataset):
        dash_context["title"] = "PSF Beads Dataset"
        (
            image_psf,
            channel_series,
        ) = concatenate_images(dataset.input.psf_beads_images)
        dash_context["image"] = image_psf
        dash_context["channel_names"] = channel_series
        dash_context["min_distance"] = (
            dataset.input.min_lateral_distance_factor
        )
        dash_context["bead_properties_df"] = get_table_file_id(
            conn,
            dataset.output.bead_properties.data_reference.omero_object_id,
        )
        dash_context["bead_km_df"] = get_table_file_id(
            conn,
            dataset.output.key_measurements.data_reference.omero_object_id,
        )
        dash_context["bead_x_profiles_df"] = get_table_file_id(
            conn,
            dataset.output.bead_profiles_x.data_reference.omero_object_id,
        )
        dash_context["bead_y_profiles_df"] = get_table_file_id(
            conn,
            dataset.output.bead_profiles_y.data_reference.omero_object_id,
        )
        dash_context["bead_z_profiles_df"] = get_table_file_id(
            conn,
            dataset.output.bead_profiles_z.data_reference.omero_object_id,
        )
        dash_context["image_id"] = dataset.input.psf_beads_images[
            0
        ].data_reference.omero_object_id
    else:
        dash_context = {}
    return dash_context


def load_dash_data_project(
    conn: BlitzGateway,
    processed_datasets: dict,
) -> (dict, str):
    dash_context = {}
    template = "OMERO_metrics/omero_views/center_view_project.html"
    df_list = []
    for k, v in processed_datasets.items():
        df = get_table_file_id(
            conn,
            v.mm_dataset.output.key_measurements.data_reference.omero_object_id,
        )
        df_list.append(df)
    dash_context["key_measurements_list"] = df_list
    return dash_context, template


def load_analysis_config(project=ProjectWrapper):
    configs = [
        ann
        for ann in project.listAnnotations(ns="OMERO-metrics/analysis_config")
        if isinstance(ann, MapAnnotationWrapper)
    ]
    if not configs:
        return None, None
    if len(configs) > 1:
        logger.error(
            f"More than one configuration"
            f" in project {project.getId()}."
            f"Using the last one saved"
        )

    return configs[-1].getId(), dict(configs[-1].getValue())


def load_image(
    image: ImageWrapper, load_array: bool = True
) -> mm_schema.Image:
    """Load an image from OMERO and return it as a schema Image"""
    time_series = None
    channel_series = mm_schema.ChannelSeries(
        channels=[
            {
                "name": c.getName(),
                "description": c.getDescription(),
                "data_reference": omero_tools.get_ref_from_object(c),
                "emission_wavelength_nm": c.getEmissionWave(),
                "excitation_wavelength_nm": c.getExcitationWave(),
            }
            for c in image.getChannels()
        ]
    )
    source_images = []
    array_data = _load_image_intensities(image) if load_array else None
    return mm_schema.Image(
        name=image.getName(),
        description=image.getDescription(),
        data_reference=omero_tools.get_ref_from_object(image),
        shape_x=image.getSizeX(),
        shape_y=image.getSizeY(),
        shape_z=image.getSizeZ(),
        shape_c=image.getSizeC(),
        shape_t=image.getSizeT(),
        acquisition_datetime=image.getAcquisitionDate(),
        voxel_size_x_micron=image.getPixelSizeX(),
        voxel_size_y_micron=image.getPixelSizeY(),
        voxel_size_z_micron=image.getPixelSizeZ(),
        time_series=time_series,
        channel_series=channel_series,
        source_images=source_images,
        # OMERO order zctyx -> microscope-metrics order TZYXC
        array_data=array_data,
    )


def _load_image_intensities(image: ImageWrapper) -> np.ndarray:
    return omero_tools.get_image_intensities(image).transpose((2, 0, 3, 4, 1))


def load_dataset_data(
    conn: BlitzGateway, dataset: DatasetWrapper
) -> mm_schema.MetricsDataset:
    pass


def get_project_data(
    collections: mm_schema.MetricsDatasetCollection,
) -> pd.DataFrame:
    data = []
    for dataset in collections.datasets:
        data.append(
            [
                dataset.__class__.__name__,
                dataset.data_reference.omero_object_type,
                dataset.data_reference.omero_object_id,
                dataset.processed,
                dataset.acquisition_datetime,
            ]
        )
    df = pd.DataFrame(
        data,
        columns=[
            "Analysis_type",
            "Omero_object_type",
            "Omero_object_id",
            "Processed",
            "Acquisition_datetime",
        ],
    )
    return df


def get_dataset_by_id(
    collections: mm_schema.MetricsDatasetCollection, dataset_id
) -> mm_schema.MetricsDataset:
    try:
        dataset = [
            i
            for i in collections.datasets
            if i.data_reference.omero_object_id == dataset_id
        ][0]
        return dataset
    except IndexError:
        return None


def get_images_intensity_profiles(
    dataset: mm_schema.MetricsDataset,
) -> pd.DataFrame:
    data = []
    for i, j in zip(
        dataset.input["field_illumination_image"],
        dataset.output["intensity_profiles"],
    ):
        data.append(
            [
                i["data_reference"]["omero_object_id"],
                j["data_reference"]["omero_object_id"],
                i["shape_c"],
            ]
        )
    df = pd.DataFrame(
        data,
        columns=["Field_illumination_image", "Intensity_profiles", "Channel"],
    )
    return df


def get_key_values(var: FieldIlluminationDataset.output) -> pd.DataFrame:
    data_dict = var.key_measurements.__dict__
    col = var.key_measurements.channel_name
    data_dict = [
        [key] + value
        for key, value in data_dict.items()
        if isinstance(value, list)
        and key
        not in [
            "name",
            "description",
            "data_reference",
            "linked_references",
            "channel_name",
        ]
    ]
    df = pd.DataFrame(data_dict, columns=["Measurements"] + col)
    return df


def concatenate_images(images: list):
    if len(images) > 1:
        image_array_0 = images[0].array_data
        channels = images[0].channel_series
        result = image_array_0
        for i in range(1, len(images)):
            image_array = images[i].array_data
            channels.channels.extend(images[i].channel_series.channels)
            result = np.concatenate((result, image_array), axis=-1)
        return result, channels
    elif len(images) == 1:
        return images[0].array_data, images[0].channel_series
    else:
        return None


def get_all_intensity_profiles(conn, data_df):
    df_01 = pd.DataFrame()
    for i, row in data_df.iterrows():
        file_id = (
            conn.getObject("FileAnnotation", row.Intensity_profiles)
            .getFile()
            .getId()
        )
        data = get_table_originalFile_id(conn, str(file_id))
        for j in range(row.Channel):
            regx_find = f"ch0{j}"
            ch = i + j
            regx_repl = f"Ch0{ch}"
            data.columns = data.columns.str.replace(regx_find, regx_repl)
        df_01 = pd.concat([df_01, data], axis=1)
    return df_01


def get_table_file_id(conn, file_annotation_id):
    file_id = (
        conn.getObject("FileAnnotation", file_annotation_id).getFile().getId()
    )
    ctx = conn.createServiceOptsDict()
    ctx.setOmeroGroup("-1")
    r = conn.getSharedResources()
    t = r.openTable(omero.model.OriginalFileI(file_id), ctx)
    data_buffer = collections.defaultdict(list)
    heads = t.getHeaders()
    target_cols = range(len(heads))
    index_buffer = []
    num_rows = t.getNumberOfRows()
    for start in range(0, num_rows):
        data = t.read(target_cols, start, start)
        for col in data.columns:
            data_buffer[col.name] += col.values
        index_buffer += data.rowNumbers
    df = pd.DataFrame.from_dict(data_buffer)
    df.index = index_buffer[0 : len(df)]
    return df
