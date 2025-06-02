"""
routes.py

Routes for the main blueprint.
"""
import flask
from pandas.core.dtypes.cast import can_hold_element

from . import main_bp
from . import requests
from . import services

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
    if document_id:
        record = requests.API.get_document(document_id=document_id)

        cached_indications = requests.Local.get_indications()
        document_indications = requests.API.get_indications(filters=f"document={document_id}")
        document_indications = services.append_field_from_matching_records(
            target_list=document_indications,
            source_list=cached_indications,
            source_field='statements_count',
            new_field_name='statements_count',
            match_key='id'
        )

        document_statements = requests.API.get_statements(filters=f"document={document_id}")
        processed_statements = services.process_statements(records=document_statements)

        return flask.render_template(
            template_name_or_list='document.html',
            document=record,
            indications=document_indications,
            statements=processed_statements
        )
    else:
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

@main_bp.route('/indications', defaults={'indication_id': None}, methods=['GET', 'POST'])
@main_bp.route('/indications/<indication_id>', endpoint='indications')
def indications(indication_id: str = None):
    if indication_id:
        record = requests.API.get_indication(indication_id=indication_id)

        indication_statements = requests.API.get_statements(filters=f"indication={indication_id}")
        processed_statements = services.process_statements(records=indication_statements)

        return flask.render_template(
            template_name_or_list='indication.html',
            indication=record,
            statements=processed_statements
        )
    else:
        records = requests.API.get_indications()
        cached_indications = requests.Local.get_indications()
        processed_indications = services.append_field_from_matching_records(
            target_list=records,
            source_list=cached_indications,
            source_field='statements_count',
            new_field_name='statements_count',
            match_key='id'
        )
        all_organizations = sorted(set(record['document']['organization']['name'] for record in records))
        return flask.render_template(
            template_name_or_list='indications.html',
            indications=processed_indications,
            all_organizations=all_organizations
        )

@main_bp.route('/organizations', defaults={'organization_id': None}, methods=['GET'])
@main_bp.route('/organizations/<organization_id>', endpoint='organizations')
def organizations(organization_id):
    if organization_id:
        record = requests.API.get_organization(organization_id=organization_id)

        cached_documents = requests.Local.get_documents()
        organization_documents = requests.API.get_documents(
            config_organization_filter=False,
            filters=f"organization={organization_id}"
        )
        organization_documents = services.append_field_from_matching_records(
            target_list=organization_documents,
            source_list=cached_documents,
            source_field='indications_count',
            new_field_name='indications_count',
            match_key='id'
        )
        organization_documents = services.append_field_from_matching_records(
            target_list=organization_documents,
            source_list=cached_documents,
            source_field='statements_count',
            new_field_name='statements_count',
            match_key='id'
        )

        cached_indications = requests.Local.get_indications()
        organization_indications = requests.API.get_indications(
            filters=f"organization={organization_id}",
            config_organization_filter=False
        )
        organization_indications = services.append_field_from_matching_records(
            target_list=organization_indications,
            source_list=cached_indications,
            source_field='statements_count',
            new_field_name='statements_count',
            match_key='id'
        )

        organization_statements = requests.API.get_statements(filters=f"organization={organization_id}")
        processed_statements = services.process_statements(records=organization_statements)

        return flask.render_template(
            template_name_or_list='organization.html',
            organization=record,
            documents=organization_documents,
            indications=organization_indications,
            statements=processed_statements
        )
    else:
        records = requests.Local.get_organizations()
        return flask.render_template(
            template_name_or_list='organizations.html',
            organizations=records
        )

@main_bp.route('/propositions', methods=['GET'])
def propositions():
    records = requests.API.get_propositions()
    processed = services.process_propositions(records=records)
    return flask.render_template(
        template_name_or_list='propositions.html',
        propositions_by_category=processed
    )

@main_bp.route('/statements', defaults={'statement_id': None}, methods=['GET'])
@main_bp.route('/statements/<statement_id>', endpoint='statements')
def statements(statement_id: str = None):
    if statement_id:
        record = requests.API.get_statement(statement_id=statement_id)
        processed = services.process_statement(records=record)
        return flask.render_template(
            template_name_or_list='statement.html',
            statement=processed
        )
    else:
        records = requests.API.get_statements(config_organization_filter=True)
        processed = services.process_statements(records=records)
        return flask.render_template(
            template_name_or_list='statements.html',
            statements=processed
        )

@main_bp.route('/therapies', defaults={'therapy_name': None}, methods=['GET', 'POST'])
@main_bp.route('/therapies/<therapy_name>', endpoint='therapies')
def therapies(therapy_name: str = None):
    if therapy_name:
        record = requests.API.get_therapy(name=therapy_name)
        processed_record = services.process_therapies(record=record)

        therapy_statements = requests.API.get_statements(
            config_organization_filter=True,
            filters=f"therapy={therapy_name}"
        )
        processed_statements = services.process_statements(records=therapy_statements)

        return flask.render_template(
            template_name_or_list='therapy.html',
            therapy=processed_record,
            statements=processed_statements
        )
    else:
        records = requests.Local.get_therapies()
        all_therapy_types = sorted(set(record['therapy_type'] for record in records))
        return flask.render_template(
            template_name_or_list='therapies.html',
            therapies=records,
            all_therapy_types=all_therapy_types
        )
