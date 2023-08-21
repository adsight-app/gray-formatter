import dynamo.visual_settings as db_settings
from docs import api
from docs_utils import LocalizedStringSchema, schema_object
from flask import Blueprint, request
from flask_utils import upload_b64_image, upload_image_from_url
from ggform_models import (
    VISUAL_SETTINGS_DEFAULT,
    VisualSettings,
    VisualSettingsDto,
    VisualSettingsWrapper
)
from ggform_pubsub import VisualSettingsUpdatedPS

settings_bp = Blueprint('Visual settings', __name__, url_prefix='/settings')
r = api.add_blueprint(settings_bp)

TEXT_FIELDS = list(VISUAL_SETTINGS_DEFAULT['Texts'].keys())

set_settings_schema = schema_object(
    {
        'WidgetVisible': bool,
        'LogoURL': str,
        'NewLogoURL': str,
        'NewLogoImage': schema_object(
            {
                'Content': str,
                'Format': str,
            }
        ),
        'BannerURL': str,
        'NewBannerURL': str,
        'NewBannerImage': schema_object(
            {
                'Content': str,
                'Format': str,
            }
        ),
        'Texts': schema_object({key: LocalizedStringSchema for key in TEXT_FIELDS}),
        'DragButton': schema_object(
            {
                'PadHor': int,
                'PadVer': int,
                'XPercentage': int,
                'YPercentage': int,
                'SizePercentage': int,
                'MaxSize': int,
            }
        ),
    },
    not_required=[
        'NewLogoURL',
        'NewLogoImage',
        'LogoURL',
        'NewBannerURL',
        'NewBannerImage',
        'BannerURL',
    ],
)


@r.route(
    '/',
    methods=['POST'],
    payload_schema=set_settings_schema,
    sends_events=[VisualSettingsUpdatedPS],
)
def set_settings() -> VisualSettingsWrapper:
    data: VisualSettingsDto = request.get_json()

    current_settings = db_settings.get_settings(request.args['ChannelID'])['Settings']

    settings: VisualSettings = {
        'WidgetVisible': data['WidgetVisible'],
        'Texts': data['Texts'],
        'LogoURL': current_settings['LogoURL'],
        'BannerURL': current_settings['BannerURL'],
        'DragButton': data['DragButton'],
    }

    if 'NewLogoImage' in data:
        settings['LogoURL'] = upload_b64_image(
            data['NewLogoImage']['Format'],
            data['NewLogoImage']['Content'],
            'extensionLogos',
        )

    if 'NewLogoURL' in data:
        settings['LogoURL'] = upload_image_from_url(
            data['NewLogoURL'], 'extensionLogos'
        )

    if 'NewBannerImage' in data:
        settings['BannerURL'] = upload_b64_image(
        data['NewBannerImage']['Format'],
        data['NewBannerImage']['Content'],
        'ggformBanners',
        )

    if 'NewBannerURL' in data:
        settings['BannerURL'] = upload_image_from_url(
        data['NewBannerURL'], 'ggformBanners')

    result = db_settings.set_settings(request.args['ChannelID'], settings)

    VisualSettingsUpdatedPS(result).send(request.args['ChannelID'])

    return result


@r.route('/', methods=['GET'])
def get_settings() -> VisualSettingsWrapper:
    return db_settings.get_settings(request.args["ChannelID"])
