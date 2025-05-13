import flask
import sqlalchemy

from . import main_bp
from . import requests

@main_bp.route('/', endpoint='index')
@main_bp.route('/index', methods=['GET', 'POST'])
def index():
    about = requests.Local.get_about()
    terms = requests.Local.get_terms()
    return flask.render_template(
        template_name_or_list='index.html',
        about=about,
        terms=terms
    )

@main_bp.route('/biomarkers', defaults={'biomarker_id': None}, methods=['GET', 'POST'])
@main_bp.route('/biomarkers/<biomarker_id>', endpoint='biomarkers')
def biomarkers(biomarker_id: str = None):
    records = requests.Local.get_biomarkers()
    all_biomarker_types = sorted(set(record['type'] for record in records))
    return flask.render_template(
        template_name_or_list='biomarkers.html',
        biomarkers=records,
        all_biomarker_types=all_biomarker_types
    )

@main_bp.route('/diseases', defaults={'disease_id': None}, methods=['GET', 'POST'])
@main_bp.route('/diseases/<disease_id>', endpoint='diseases')
def diseases(disease_id: str = None):
    records = requests.Local.get_diseases()
    return flask.render_template(
        template_name_or_list='diseases.html',
        diseases=records
    )

@main_bp.route('/documents', defaults={'document_id': None}, methods=['GET', 'POST'])
@main_bp.route('/documents/<document_id>', endpoint='documents')
def documents(document_id: str = None):
    records = requests.Local.get_documents()
    all_organizations = sorted(set(record['organization_name'] for record in records))
    return flask.render_template(
        template_name_or_list='documents.html',
        documents=records,
        all_organizations=all_organizations
    )

@main_bp.route('/genes', defaults={'gene_name': None}, methods=['GET', 'POST'])
@main_bp.route('/genes/<gene_name>', endpoint='genes')
def genes(gene_name: str = None):
    if gene_name:
        record = requests.API.get_gene(name=gene_name)
        return flask.render_template(
            template_name_or_list='gene.html',
            gene=record
        )
    else:
        records = requests.Local.get_genes()
        return flask.render_template(
            template_name_or_list='genes.html',
            genes=records
        )

@main_bp.route('/therapies', defaults={'therapy_name': None}, methods=['GET', 'POST'])
@main_bp.route('/therapies/<therapy_name>', endpoint='therapies')
def therapies(therapy_name: str = None):
    records = requests.Local.get_therapies()
    all_therapy_types = sorted(set(record['therapy_type'] for record in records))
    return flask.render_template(
        template_name_or_list='therapies.html',
        therapies=records,
        all_therapy_types=all_therapy_types
    )
