"""
routes.py

Routes for the main blueprint.
"""

import flask
from pandas.core.dtypes.cast import can_hold_element

from . import main_bp
from . import requests
from . import services


@main_bp.route("/", endpoint="index")
@main_bp.route("/index", methods=["GET", "POST"])
def index():
    about = requests.Local.get_about()
    terms = requests.Local.get_terms()
    return flask.render_template(
        template_name_or_list="index.html", about=about, terms=terms
    )


@main_bp.route("/about", methods=["GET", "POST"])
def about():
    return flask.render_template(
        template_name_or_list="about.html",
    )


@main_bp.route(
    "/biomarkers", defaults={"biomarker_name": None}, methods=["GET", "POST"]
)
@main_bp.route("/biomarkers/<biomarker_name>", endpoint="biomarkers")
def biomarkers(biomarker_name: str | None = None):
    if biomarker_name:
        record = requests.API.get_biomarker(biomarker_name=biomarker_name)
        # processed_record = services.process_biomarker(record=record)
        processed_record = record

        biomarker_propositions = requests.API.get_search_results(
            config_organization_filter=True,
            filters=f"biomarker={biomarker_name.replace(' ', '%20')}",
        )
        processed_propositions = services.process_propositions(
            records=biomarker_propositions
        )

        return flask.render_template(
            template_name_or_list="biomarker.html",
            biomarker=processed_record,
            propositions_by_category=processed_propositions,
        )
    else:
        records = requests.Local.get_biomarkers()
        all_biomarker_types = sorted(set(record["type"] for record in records))
        return flask.render_template(
            template_name_or_list="biomarkers.html",
            biomarkers=records,
            all_biomarker_types=all_biomarker_types,
        )


@main_bp.route("/diseases", defaults={"disease_name": None}, methods=["GET", "POST"])
@main_bp.route("/diseases/<disease_name>", endpoint="diseases")
def diseases(disease_name: str = None):
    if disease_name:
        record = requests.API.get_disease(name=disease_name)
        processed_record = record
        # processed_record = services.process_disease(record=record)

        disease_propositions = requests.API.get_search_results(
            config_organization_filter=True,
            filters=f"disease={disease_name}",
        )
        processed_propositions = services.process_propositions(
            records=disease_propositions
        )

        return flask.render_template(
            template_name_or_list="disease.html",
            disease=processed_record,
            propositions_by_category=processed_propositions,
        )
    else:
        records = requests.Local.get_diseases()
        return flask.render_template(
            template_name_or_list="diseases.html", diseases=records
        )


@main_bp.route("/documents", defaults={"document_id": None}, methods=["GET", "POST"])
@main_bp.route("/documents/<document_id>", endpoint="documents")
def documents(document_id: str | None = None):
    if document_id:
        record = requests.API.get_document(document_id=document_id)

        cached_indications = requests.Local.get_indications()
        document_indications = requests.API.get_indications(
            filters=f"document={document_id}"
        )
        document_indications = services.append_field_from_matching_records(
            target_list=document_indications,
            source_list=cached_indications,
            source_field="statements_count",
            new_field_name="statements_count",
            match_key="id",
        )

        document_propositions = requests.API.get_search_results(
            config_organization_filter=True, filters=f"document={document_id}"
        )
        processed_propositions = services.process_propositions(
            records=document_propositions
        )

        return flask.render_template(
            template_name_or_list="document.html",
            document=record,
            indications=document_indications,
            propositions_by_category=processed_propositions,
        )
    else:
        records = requests.Local.get_documents()
        all_organizations = sorted(set(record["agent_name"] for record in records))
        return flask.render_template(
            template_name_or_list="documents.html",
            documents=records,
            all_organizations=all_organizations,
        )


@main_bp.route("/genes", defaults={"gene_symbol": None}, methods=["GET", "POST"])
@main_bp.route("/genes/<gene_symbol>", endpoint="genes")
def genes(gene_symbol: str | None = None):
    if gene_symbol:
        record = requests.API.get_gene(name=gene_symbol)
        processed_record = services.process_gene(record=record)

        cached_biomarkers = requests.Local.get_biomarkers()
        gene_biomarkers = requests.API.get_biomarkers(
            config_organization_filter=True, filters=f"gene={gene_symbol}"
        )
        gene_biomarkers = services.append_field_from_matching_records(
            target_list=gene_biomarkers,
            source_list=cached_biomarkers,
            source_field="propositions_count",
            new_field_name="propositions_count",
            match_key="id",
        )
        gene_biomarkers = services.append_field_from_matching_records(
            target_list=gene_biomarkers,
            source_list=cached_biomarkers,
            source_field="statements_count",
            new_field_name="statements_count",
            match_key="id",
        )

        gene_propositions = requests.API.get_search_results(
            config_organization_filter=True, filters=f"gene={gene_symbol}"
        )
        processed_propositions = services.process_propositions(
            records=gene_propositions
        )

        return flask.render_template(
            template_name_or_list="gene.html",
            gene=processed_record,
            biomarkers=gene_biomarkers,
            propositions_by_category=processed_propositions,
        )
    else:
        records = requests.Local.get_genes()
        return flask.render_template(template_name_or_list="genes.html", genes=records)


@main_bp.route("/indications", defaults={"indication_id": None}, methods=["GET", "POST"])
@main_bp.route("/indications/<indication_id>", endpoint="indications")
def indications(indication_id: str | None = None):
    if indication_id:
        record = requests.API.get_indication(indication_id=indication_id)

        indication_propositions = requests.API.get_search_results(
            config_organization_filter=False,
            filters=f"indication={indication_id}",
        )
        processed_propositions = services.process_propositions(
            records=indication_propositions
        )

        return flask.render_template(
            template_name_or_list="indication.html",
            indication=record,
            propositions_by_category=processed_propositions,
        )
    else:
        records = requests.API.get_indications(config_organization_filter=True)
        cached_indications = requests.Local.get_indications()
        processed_indications = services.append_field_from_matching_records(
            target_list=records,
            source_list=cached_indications,
            source_field="statements_count",
            new_field_name="statements_count",
            match_key="id",
        )
        for indication in processed_indications:
            if not indication.get("statements_count", None):
                indication["statements_count"] = 0
        all_organizations = sorted(
            set(record["document"]["agent"]["name"] for record in records)
        )
        return flask.render_template(
            template_name_or_list="indications.html",
            indications=processed_indications,
            all_organizations=all_organizations,
        )


@main_bp.route("/organizations", defaults={"organization_id": None}, methods=["GET"])
@main_bp.route("/organizations/<organization_id>", endpoint="organizations")
def organizations(organization_id):
    if organization_id:
        record = requests.API.get_organization(organization_id=organization_id)
        cached_documents = requests.Local.get_documents()
        organization_documents = requests.API.get_documents(
            config_organization_filter=False,
            filters=f"agent_id={organization_id}",
        )
        organization_documents = services.append_field_from_matching_records(
            target_list=organization_documents,
            source_list=cached_documents,
            source_field="indications_count",
            new_field_name="indications_count",
            match_key="id",
        )
        organization_documents = services.append_field_from_matching_records(
            target_list=organization_documents,
            source_list=cached_documents,
            source_field="statements_count",
            new_field_name="statements_count",
            match_key="id",
        )

        cached_indications = requests.Local.get_indications()
        organization_indications = requests.API.get_indications(
            filters=f"agent_id={organization_id}",
            config_organization_filter=False,
        )
        organization_indications = services.append_field_from_matching_records(
            target_list=organization_indications,
            source_list=cached_indications,
            source_field="statements_count",
            new_field_name="statements_count",
            match_key="id",
        )

        organization_propositions = requests.API.get_search_results(
            config_organization_filter=True,
            filters=f"",
            # Filter for query will be contained already within organization filters
            # of the browser's instance
        )
        filtered_propositions = services.filter_search_results_required_organization(
            records=organization_propositions,
            organization_id=organization_id,
        )
        processed_propositions = services.process_propositions(
            records=filtered_propositions
        )
        response_organizations = services.extract_organizations(
            propositions=processed_propositions
        )

        return flask.render_template(
            template_name_or_list="organization.html",
            organization=record,
            documents=organization_documents,
            indications=organization_indications,
            propositions_by_category=processed_propositions,
            organizations=response_organizations,
        )
    else:
        records = requests.Local.get_organizations()
        return flask.render_template(
            template_name_or_list="organizations.html", 
            organizations=records,
        )


@main_bp.route("/propositions", defaults={"proposition_id": None}, methods=["GET"])
@main_bp.route("/propositions/<proposition_id>", endpoint="propositions")
def propositions(proposition_id: str | None = None):
    if proposition_id:
        record = requests.API.get_proposition(proposition_id=proposition_id)
        processed = services.process_proposition(record=record)

        proposition_statements = requests.API.get_statements(
            config_organization_filter=True, filters=f"proposition_id={proposition_id}"
        )
        processed_statements = services.process_statements(
            records=proposition_statements
        )

        return flask.render_template(
            template_name_or_list="proposition.html",
            proposition=processed,
            statements=processed_statements,
            organization_filters=requests.API.get_config_organization_filters(),
        )
    records = requests.API.get_propositions()
    processed = services.process_propositions(records=records)
    return flask.render_template(
        template_name_or_list="propositions.html", propositions_by_category=processed
    )


@main_bp.route("/search", methods=["GET"])
def search():
    records = requests.API.get_search_results(config_organization_filter=True)
    processed = services.process_propositions(records=records)
    response_organizations = services.extract_organizations(propositions=processed)
    return flask.render_template(
        template_name_or_list="search.html",
        propositions_by_category=processed,
        organizations=response_organizations,
    )


@main_bp.route("/statements", defaults={"statement_id": None}, methods=["GET"])
@main_bp.route("/statements/<statement_id>", endpoint="statements")
def statements(statement_id: str | None = None):
    if statement_id:
        record = requests.API.get_statement(statement_id=statement_id)
        processed = services.process_statement(record=record)
        return flask.render_template(
            template_name_or_list="statement.html", 
            statement=processed,
        )
    else:
        records = requests.API.get_statements(config_organization_filter=True)
        processed = services.process_statements(records=records)
        return flask.render_template(
            template_name_or_list="statements.html", statements=processed
        )


@main_bp.route("/therapies", defaults={"therapy_name": None}, methods=["GET", "POST"])
@main_bp.route("/therapies/<therapy_name>", endpoint="therapies")
def therapies(therapy_name: str | None = None):
    if therapy_name:
        record = requests.API.get_therapy(name=therapy_name)
        processed_record = services.process_therapy(record=record)

        therapy_propositions = requests.API.get_search_results(
            config_organization_filter=True, filters=f"therapy={therapy_name}"
        )
        processed_propositions = services.process_propositions(
            records=therapy_propositions
        )

        return flask.render_template(
            template_name_or_list="therapy.html",
            therapy=processed_record,
            propositions_by_category=processed_propositions,
        )
    else:
        records = requests.Local.get_therapies()
        all_therapy_types = sorted(set(record["therapy_type"] for record in records))
        return flask.render_template(
            template_name_or_list="therapies.html",
            therapies=records,
            all_therapy_types=all_therapy_types,
        )
