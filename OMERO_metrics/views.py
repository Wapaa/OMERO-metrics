from omeroweb.webclient.decorators import login_required, render_response
from OMERO_metrics.tools.data_managers import (
    DatasetManager,
    ProjectManager,
    ImageManager,
)
from django.shortcuts import render
from OMERO_metrics.forms import UploadFileForm
import numpy as np
from OMERO_metrics.tools.omero_tools import (
    create_image_from_numpy_array,
    get_ref_from_object,
)
from OMERO_metrics.tools.load import load_config_file_data
from OMERO_metrics.tools.dump import dump_config_input_parameters
from OMERO_metrics.tools.load import load_image
from microscopemetrics_schema import datamodel as mm_schema
from microscopemetrics.analyses import field_illumination, psf_beads
from OMERO_metrics.tools.dump import dump_dataset
import omero
import logging

logger = logging.getLogger(__name__)

DATA_TYPE = {
    "FieldIlluminationInputParameters": [
        "FieldIlluminationDataset",
        "FieldIlluminationInputData",
        "field_illumination_image",
        field_illumination.analyse_field_illumination,
    ],
    "PSFBeadsInputParameters": [
        "PSFBeadsDataset",
        "PSFBeadsInputData",
        "psf_beads_images",
        psf_beads.analyse_psf_beads,
    ],
}


@login_required()
def upload_image(request, conn=None, **kwargs):
    if request.method == "POST":
        form = UploadFileForm(request.POST, request.FILES)
        id_image = ""
        type_image = ""
        if form.is_valid():
            file = request.FILES["file"]
            title = form.cleaned_data["title"]
            dataset_id = form.cleaned_data["dataset_id"]
            dataset = conn.getObject("Dataset", int(dataset_id))
            group_id = dataset.getDetails().getGroup().getId()
            conn.SERVICE_OPTS.setOmeroGroup(group_id)
            type_image = file.name
            ima = np.load(file)
            image = ima.transpose((1, 4, 0, 2, 3))
            ima_wrapper = create_image_from_numpy_array(
                conn, image, title, dataset=dataset
            )
            id_image = ima_wrapper.getId()
        return render(
            request,
            "OMERO_metrics/success.html",
            {
                "type": type_image,
                "id_dataset": dataset.getId(),
                "id_image": id_image,
            },
        )
    else:
        form = UploadFileForm()
    return render(
        request, "OMERO_metrics/upload_image_omero.html", {"form": form}
    )


@login_required()
def index(request, conn=None, **kwargs):
    experimenter = conn.getUser()
    context = {
        "firstName": experimenter.firstName,
        "lastName": experimenter.lastName,
        "experimenterId": experimenter.id,
    }
    return render(request, "OMERO_metrics/index.html", context)


@login_required()
def session_state_view(request, template_name, **kwargs):
    "Example view that exhibits the use of sessions to store state"
    session = request.session
    omero_views_count = session.get("django_plotly_dash", {})
    ind_use = omero_views_count.get("ind_use", 0)
    ind_use += 1
    omero_views_count["ind_use"] = ind_use
    context = {"ind_use": ind_use}
    session["django_plotly_dash"] = omero_views_count
    return render(request, template_name=template_name, context=context)


def web_gateway_templates(request, base_template):
    """Simply return the named template. Similar functionality to
    django.views.generic.simple.direct_to_template"""
    template_name = "OMERO_metrics/web_gateway/%s.html" % base_template
    return render(request, template_name, {})


@login_required()
@render_response()
def webclient_templates(request, base_template, **kwargs):
    """Simply return the named template.
    Similar functionality to
    django.views.generic.simple.direct_to_template"""
    template_name = "OMERO_metrics/web_gateway/%s.html" % base_template
    return {"template": template_name}


@login_required()
def image_rois(request, image_id, conn=None, **kwargs):
    """Simply shows a page of ROI
    thumbnails for the specified image"""
    roi_ids = image_id
    return render(
        request,
        "OMERO_metrics/omero_views/image_rois.html",
        {"roiIds": roi_ids},
    )


@login_required()
def center_viewer_image(request, image_id, conn=None, **kwargs):
    dash_context = request.session.get("django_plotly_dash", dict())
    image_wrapper = conn.getObject("Image", image_id)
    group_id = conn.getGroupFromContext().getName()
    print(
        f"IMAGE VIEW----------------------------------------{group_id}---------------"
    )
    im = ImageManager(conn, image_wrapper)
    im.load_data()
    im.visualize_data()
    dash_context["context"] = im.context
    template = im.template
    request.session["django_plotly_dash"] = dash_context
    return render(request, template_name=template)


@login_required()
def center_viewer_project(request, project_id, conn=None, **kwargs):
    # request["conn"] = conn
    # conn.SERVICE_OPTS.setOmeroGroup("-1")
    project_wrapper = conn.getObject("Project", project_id)
    group_id = conn.getGroupFromContext().getName()
    print(f"PROJECT VIEW--------------{group_id}--------------------------")
    conn.SERVICE_OPTS.setOmeroGroup(group_id)
    pm = ProjectManager(conn, project_wrapper)
    pm.load_data()
    pm.is_homogenized()
    pm.load_config_file()
    pm.check_processed_data()
    pm.visualize_data()
    context = pm.context
    template = pm.template
    dash_context = request.session.get("django_plotly_dash", dict())
    dash_context["context"] = context
    dash_context["context"]["project_id"] = project_id
    request.session["django_plotly_dash"] = dash_context
    return render(request, template_name=template, context=context)


@login_required()
def center_viewer_group(request, conn=None, **kwargs):
    group2 = conn.SERVICE_OPTS.getOmeroGroup()
    group = conn.getGroupFromContext()
    group_id = conn.getGroupFromContext().getName()
    group_name = group.getName()
    print(
        f"GROUP VIEW----------------------------------------{group_id}---------------"
    )

    group_description = group.getDescription()
    context = {
        "group_id": group_id,
        "group_name": group2,
        "group_description": group_description,
    }
    return render(
        request, "OMERO_metrics/omero_views/center_view_group.html", context
    )


@login_required()
def center_viewer_dataset(request, dataset_id, conn=None, **kwargs):
    dash_context = request.session.get("django_plotly_dash", dict())
    dataset_wrapper = conn.getObject("Dataset", dataset_id)
    group_id = conn.getGroupFromContext().getName()
    print(
        f"DATASET VIEW----------------------------------------{group_id}---------------"
    )
    dm = DatasetManager(conn, dataset_wrapper, load_images=True)
    dm.load_data()
    dm.is_processed()
    dm.visualize_data()
    dash_context["context"] = dm.context
    template = dm.template
    request.session["django_plotly_dash"] = dash_context
    return render(request, template_name=template)


@login_required()
def microscope_view(request, conn=None, **kwargs):
    """Simply shows a page of ROI thumbnails for
    the specified image"""
    return render(request, "OMERO_metrics/microscope.html")


@login_required()
def save_config(request, conn=None, **kwargs):
    try:
        project_id = kwargs["project_id"]
        mm_input_parameters = kwargs["input_parameters"]
        mm_sample = kwargs["sample"]
        project_wrapper = conn.getObject("Project", project_id)
        group_id = project_wrapper.getDetails().getGroup().getId()
        conn.SERVICE_OPTS.setOmeroGroup(group_id)
        setup = load_config_file_data(conn, project_wrapper)
        if setup is None:
            try:
                dump_config_input_parameters(
                    conn, mm_input_parameters, mm_sample, project_wrapper
                )
                return (
                    "File saved successfully, Re-click on the project to see the changes",
                    "green",
                )
            except Exception as e:
                if isinstance(e, omero.SecurityViolation):
                    return (
                        "You don't have the necessary permissions to save the configuration. ",
                        "red",
                    )
                else:
                    return str(e), "red"

        else:
            return (
                "Failed to save file, a configuration file already exists",
                "red",
            )
    except Exception as e:
        return str(e), "red"


@login_required()
def run_analysis_view(request, conn=None, **kwargs):
    try:
        co = conn.getEventContext()
        dataset_wrapper = conn.getObject("Dataset", kwargs["dataset_id"])
        project_wrapper = dataset_wrapper.getParent()
        group_id = project_wrapper.getDetails().getGroup().getId()
        group_id2 = conn.getGroupFromContext().getName()
        group_id3 = dataset_wrapper.getDetails().getGroup().getName()
        print(f"Group from dataset           4: {group_id3}")
        print(f"Group context          3: {group_id2}")
        print(
            f"Group project           1: {project_wrapper.getDetails().getGroup().getName()}"
        )
        # g_id = dataset_wrapper.getDetails().getGroup().getId()
        conn.SERVICE_OPTS.setOmeroGroup(int(group_id))
        # conn.setGroupForSession(int(g_id))
        co5 = conn.getEventContext()

        print()
        co5.setGroup(group_id)
        c = co5
        print(f"Group ID           2: {conn.getGroupFromContext().getName()}")
        list_images = kwargs["list_images"]
        list_mm_images = [
            load_image(conn.getObject("Image", int(i))) for i in list_images
        ]
        mm_sample = kwargs["mm_sample"]
        mm_input_parameters = kwargs["mm_input_parameters"]
        input_data = getattr(
            mm_schema, DATA_TYPE[mm_input_parameters.class_name][1]
        )
        input_data = input_data(
            **{DATA_TYPE[mm_input_parameters.class_name][2]: list_mm_images}
        )
        mm_microscope = mm_schema.Microscope(
            name=project_wrapper.getDetails().getGroup().getName()
        )
        mm_experimenter = mm_schema.Experimenter(
            orcid="0000-0002-1825-0097", name=conn.getUser().getName()
        )
        mm_dataset = getattr(
            mm_schema, DATA_TYPE[mm_input_parameters.class_name][0]
        )
        mm_dataset = mm_dataset(
            name=dataset_wrapper.getName(),
            description=dataset_wrapper.getDescription(),
            data_reference=get_ref_from_object(dataset_wrapper),
            input_parameters=mm_input_parameters,
            microscope=mm_microscope,
            sample=mm_sample,
            input_data=input_data,
            acquisition_datetime=dataset_wrapper.getDate().strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            experimenter=mm_experimenter,
        )
        run_status = DATA_TYPE[mm_input_parameters.class_name][3](mm_dataset)
        if run_status and mm_dataset.processed:
            try:
                dump_dataset(
                    conn=conn,
                    dataset=mm_dataset,
                    target_project=project_wrapper,
                    dump_as_project_file_annotation=True,
                    dump_as_dataset_file_annotation=True,
                    dump_input_images=False,
                    dump_analysis=True,
                )
                return "Analysis completed successfully", "green"
            except Exception as e:
                return (
                    e.msg,
                    "red",
                )
        else:
            logger.error("Analysis failed")
            return "We couldn't process the analysis.", "red"
    except Exception as e:
        return str(e), "red"
