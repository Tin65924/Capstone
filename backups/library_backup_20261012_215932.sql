--
-- PostgreSQL database dump
--

\restrict vo2G7w67oxLKOnsfFx1kMwYHMZpc3qsbZHl5OHl9YIpRIWh6SkdTfAHEvfuhZGC

-- Dumped from database version 18.1
-- Dumped by pg_dump version 18.1

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

ALTER TABLE IF EXISTS ONLY public.user_favorites DROP CONSTRAINT IF EXISTS user_favorites_user_id_fkey;
ALTER TABLE IF EXISTS ONLY public.user_favorites DROP CONSTRAINT IF EXISTS user_favorites_book_id_fkey;
ALTER TABLE IF EXISTS ONLY public.user_accounts DROP CONSTRAINT IF EXISTS user_accounts_updated_by_fkey;
ALTER TABLE IF EXISTS ONLY public.user_accounts DROP CONSTRAINT IF EXISTS user_accounts_role_id_fkey;
ALTER TABLE IF EXISTS ONLY public.reservation_queue DROP CONSTRAINT IF EXISTS reservation_queue_updated_by_fkey;
ALTER TABLE IF EXISTS ONLY public.reservation_queue DROP CONSTRAINT IF EXISTS reservation_queue_borrower_id_fkey;
ALTER TABLE IF EXISTS ONLY public.reservation_queue DROP CONSTRAINT IF EXISTS reservation_queue_book_id_fkey;
ALTER TABLE IF EXISTS ONLY public.request_records DROP CONSTRAINT IF EXISTS request_records_updated_by_fkey;
ALTER TABLE IF EXISTS ONLY public.request_records DROP CONSTRAINT IF EXISTS request_records_reviewed_by_fkey;
ALTER TABLE IF EXISTS ONLY public.request_records DROP CONSTRAINT IF EXISTS request_records_requester_id_fkey;
ALTER TABLE IF EXISTS ONLY public.request_records DROP CONSTRAINT IF EXISTS request_records_matched_book_id_fkey;
ALTER TABLE IF EXISTS ONLY public.procurement_log DROP CONSTRAINT IF EXISTS procurement_log_updated_by_fkey;
ALTER TABLE IF EXISTS ONLY public.procurement_log DROP CONSTRAINT IF EXISTS procurement_log_request_id_fkey;
ALTER TABLE IF EXISTS ONLY public.procurement_log DROP CONSTRAINT IF EXISTS procurement_log_book_id_fkey;
ALTER TABLE IF EXISTS ONLY public.notification_log DROP CONSTRAINT IF EXISTS notification_log_updated_by_fkey;
ALTER TABLE IF EXISTS ONLY public.notification_log DROP CONSTRAINT IF EXISTS notification_log_recipient_id_fkey;
ALTER TABLE IF EXISTS ONLY public.library_settings DROP CONSTRAINT IF EXISTS library_settings_updated_by_fkey;
ALTER TABLE IF EXISTS ONLY public.inventory_status DROP CONSTRAINT IF EXISTS inventory_status_session_id_fkey;
ALTER TABLE IF EXISTS ONLY public.inventory_status DROP CONSTRAINT IF EXISTS inventory_status_checked_by_fkey;
ALTER TABLE IF EXISTS ONLY public.inventory_status DROP CONSTRAINT IF EXISTS inventory_status_accession_id_fkey;
ALTER TABLE IF EXISTS ONLY public.inventory_sessions DROP CONSTRAINT IF EXISTS inventory_sessions_updated_by_fkey;
ALTER TABLE IF EXISTS ONLY public.inventory_sessions DROP CONSTRAINT IF EXISTS inventory_sessions_librarian_id_fkey;
ALTER TABLE IF EXISTS ONLY public.circulation_records DROP CONSTRAINT IF EXISTS circulation_records_updated_by_fkey;
ALTER TABLE IF EXISTS ONLY public.circulation_records DROP CONSTRAINT IF EXISTS circulation_records_processed_by_fkey;
ALTER TABLE IF EXISTS ONLY public.circulation_records DROP CONSTRAINT IF EXISTS circulation_records_borrower_id_fkey;
ALTER TABLE IF EXISTS ONLY public.circulation_records DROP CONSTRAINT IF EXISTS circulation_records_book_id_fkey;
ALTER TABLE IF EXISTS ONLY public.circulation_records DROP CONSTRAINT IF EXISTS circulation_records_accession_id_fkey;
ALTER TABLE IF EXISTS ONLY public.borrowers DROP CONSTRAINT IF EXISTS borrowers_user_id_fkey;
ALTER TABLE IF EXISTS ONLY public.borrowers DROP CONSTRAINT IF EXISTS borrowers_updated_by_fkey;
ALTER TABLE IF EXISTS ONLY public.book_catalog DROP CONSTRAINT IF EXISTS book_catalog_updated_by_fkey;
ALTER TABLE IF EXISTS ONLY public.audit_trail DROP CONSTRAINT IF EXISTS audit_trail_user_id_fkey;
ALTER TABLE IF EXISTS ONLY public.analytics_cache DROP CONSTRAINT IF EXISTS analytics_cache_generated_by_fkey;
ALTER TABLE IF EXISTS ONLY public.accession_log DROP CONSTRAINT IF EXISTS accession_log_updated_by_fkey;
ALTER TABLE IF EXISTS ONLY public.accession_log DROP CONSTRAINT IF EXISTS accession_log_librarian_id_fkey;
ALTER TABLE IF EXISTS ONLY public.accession_log DROP CONSTRAINT IF EXISTS accession_log_book_id_fkey;
DROP INDEX IF EXISTS public.uq_pending_req;
DROP INDEX IF EXISTS public.uq_active_reservation_per_book_borrower;
DROP INDEX IF EXISTS public.uq_active_queue_pos;
DROP INDEX IF EXISTS public.uq_active_loan_per_book_borrower;
DROP INDEX IF EXISTS public.uq_active_loan_per_accession;
DROP INDEX IF EXISTS public.idx_user_accounts_status;
DROP INDEX IF EXISTS public.idx_user_accounts_role;
DROP INDEX IF EXISTS public.idx_reservation_status;
DROP INDEX IF EXISTS public.idx_reservation_book;
DROP INDEX IF EXISTS public.idx_requests_status;
DROP INDEX IF EXISTS public.idx_requests_requester;
DROP INDEX IF EXISTS public.idx_notif_recipient;
DROP INDEX IF EXISTS public.idx_inventory_accession;
DROP INDEX IF EXISTS public.idx_circ_status;
DROP INDEX IF EXISTS public.idx_circ_borrow_date;
DROP INDEX IF EXISTS public.idx_circ_book;
DROP INDEX IF EXISTS public.idx_circ_accession;
DROP INDEX IF EXISTS public.idx_borrowers_department;
DROP INDEX IF EXISTS public.idx_book_catalog_year;
DROP INDEX IF EXISTS public.idx_book_catalog_title;
DROP INDEX IF EXISTS public.idx_book_catalog_subject;
DROP INDEX IF EXISTS public.idx_book_catalog_status;
DROP INDEX IF EXISTS public.idx_book_catalog_isbn;
DROP INDEX IF EXISTS public.idx_book_catalog_author;
DROP INDEX IF EXISTS public.idx_audit_user;
DROP INDEX IF EXISTS public.idx_audit_time;
DROP INDEX IF EXISTS public.idx_accession_log_number;
DROP INDEX IF EXISTS public.idx_accession_log_book;
ALTER TABLE IF EXISTS ONLY public.user_favorites DROP CONSTRAINT IF EXISTS user_favorites_user_id_book_id_key;
ALTER TABLE IF EXISTS ONLY public.user_favorites DROP CONSTRAINT IF EXISTS user_favorites_pkey;
ALTER TABLE IF EXISTS ONLY public.user_accounts DROP CONSTRAINT IF EXISTS user_accounts_pkey;
ALTER TABLE IF EXISTS ONLY public.user_accounts DROP CONSTRAINT IF EXISTS user_accounts_oauth_sub_key;
ALTER TABLE IF EXISTS ONLY public.user_accounts DROP CONSTRAINT IF EXISTS user_accounts_email_key;
ALTER TABLE IF EXISTS ONLY public.roles DROP CONSTRAINT IF EXISTS roles_role_name_key;
ALTER TABLE IF EXISTS ONLY public.roles DROP CONSTRAINT IF EXISTS roles_pkey;
ALTER TABLE IF EXISTS ONLY public.reservation_queue DROP CONSTRAINT IF EXISTS reservation_queue_pkey;
ALTER TABLE IF EXISTS ONLY public.request_records DROP CONSTRAINT IF EXISTS request_records_pkey;
ALTER TABLE IF EXISTS ONLY public.procurement_log DROP CONSTRAINT IF EXISTS procurement_log_pkey;
ALTER TABLE IF EXISTS ONLY public.notification_log DROP CONSTRAINT IF EXISTS notification_log_pkey;
ALTER TABLE IF EXISTS ONLY public.library_settings DROP CONSTRAINT IF EXISTS library_settings_pkey;
ALTER TABLE IF EXISTS ONLY public.inventory_status DROP CONSTRAINT IF EXISTS inventory_status_pkey;
ALTER TABLE IF EXISTS ONLY public.inventory_sessions DROP CONSTRAINT IF EXISTS inventory_sessions_pkey;
ALTER TABLE IF EXISTS ONLY public.departments DROP CONSTRAINT IF EXISTS departments_pkey;
ALTER TABLE IF EXISTS ONLY public.departments DROP CONSTRAINT IF EXISTS departments_dept_type_name_key;
ALTER TABLE IF EXISTS ONLY public.circulation_records DROP CONSTRAINT IF EXISTS circulation_records_pkey;
ALTER TABLE IF EXISTS ONLY public.borrowers DROP CONSTRAINT IF EXISTS borrowers_user_id_key;
ALTER TABLE IF EXISTS ONLY public.borrowers DROP CONSTRAINT IF EXISTS borrowers_pkey;
ALTER TABLE IF EXISTS ONLY public.borrowers DROP CONSTRAINT IF EXISTS borrowers_id_number_key;
ALTER TABLE IF EXISTS ONLY public.book_catalog DROP CONSTRAINT IF EXISTS book_catalog_pkey;
ALTER TABLE IF EXISTS ONLY public.backup_log DROP CONSTRAINT IF EXISTS backup_log_pkey;
ALTER TABLE IF EXISTS ONLY public.audit_trail DROP CONSTRAINT IF EXISTS audit_trail_pkey;
ALTER TABLE IF EXISTS ONLY public.analytics_cache DROP CONSTRAINT IF EXISTS analytics_cache_pkey;
ALTER TABLE IF EXISTS ONLY public.accession_log DROP CONSTRAINT IF EXISTS accession_log_pkey;
ALTER TABLE IF EXISTS ONLY public.accession_log DROP CONSTRAINT IF EXISTS accession_log_accession_number_key;
ALTER TABLE IF EXISTS public.user_favorites ALTER COLUMN favorite_id DROP DEFAULT;
ALTER TABLE IF EXISTS public.user_accounts ALTER COLUMN user_id DROP DEFAULT;
ALTER TABLE IF EXISTS public.roles ALTER COLUMN role_id DROP DEFAULT;
ALTER TABLE IF EXISTS public.reservation_queue ALTER COLUMN reservation_id DROP DEFAULT;
ALTER TABLE IF EXISTS public.request_records ALTER COLUMN request_id DROP DEFAULT;
ALTER TABLE IF EXISTS public.procurement_log ALTER COLUMN procurement_id DROP DEFAULT;
ALTER TABLE IF EXISTS public.notification_log ALTER COLUMN notification_id DROP DEFAULT;
ALTER TABLE IF EXISTS public.inventory_status ALTER COLUMN inventory_id DROP DEFAULT;
ALTER TABLE IF EXISTS public.inventory_sessions ALTER COLUMN session_id DROP DEFAULT;
ALTER TABLE IF EXISTS public.departments ALTER COLUMN department_id DROP DEFAULT;
ALTER TABLE IF EXISTS public.circulation_records ALTER COLUMN circulation_id DROP DEFAULT;
ALTER TABLE IF EXISTS public.borrowers ALTER COLUMN borrower_id DROP DEFAULT;
ALTER TABLE IF EXISTS public.book_catalog ALTER COLUMN book_id DROP DEFAULT;
ALTER TABLE IF EXISTS public.backup_log ALTER COLUMN backup_id DROP DEFAULT;
ALTER TABLE IF EXISTS public.audit_trail ALTER COLUMN log_id DROP DEFAULT;
ALTER TABLE IF EXISTS public.analytics_cache ALTER COLUMN cache_id DROP DEFAULT;
ALTER TABLE IF EXISTS public.accession_log ALTER COLUMN accession_id DROP DEFAULT;
DROP SEQUENCE IF EXISTS public.user_favorites_favorite_id_seq;
DROP TABLE IF EXISTS public.user_favorites;
DROP SEQUENCE IF EXISTS public.user_accounts_user_id_seq;
DROP TABLE IF EXISTS public.user_accounts;
DROP SEQUENCE IF EXISTS public.roles_role_id_seq;
DROP TABLE IF EXISTS public.roles;
DROP SEQUENCE IF EXISTS public.reservation_queue_reservation_id_seq;
DROP TABLE IF EXISTS public.reservation_queue;
DROP SEQUENCE IF EXISTS public.request_records_request_id_seq;
DROP TABLE IF EXISTS public.request_records;
DROP SEQUENCE IF EXISTS public.procurement_log_procurement_id_seq;
DROP TABLE IF EXISTS public.procurement_log;
DROP SEQUENCE IF EXISTS public.notification_log_notification_id_seq;
DROP TABLE IF EXISTS public.notification_log;
DROP TABLE IF EXISTS public.library_settings;
DROP SEQUENCE IF EXISTS public.inventory_status_inventory_id_seq;
DROP TABLE IF EXISTS public.inventory_status;
DROP SEQUENCE IF EXISTS public.inventory_sessions_session_id_seq;
DROP TABLE IF EXISTS public.inventory_sessions;
DROP SEQUENCE IF EXISTS public.departments_department_id_seq;
DROP TABLE IF EXISTS public.departments;
DROP SEQUENCE IF EXISTS public.circulation_records_circulation_id_seq;
DROP TABLE IF EXISTS public.circulation_records;
DROP SEQUENCE IF EXISTS public.borrowers_borrower_id_seq;
DROP TABLE IF EXISTS public.borrowers;
DROP SEQUENCE IF EXISTS public.book_catalog_book_id_seq;
DROP TABLE IF EXISTS public.book_catalog;
DROP SEQUENCE IF EXISTS public.backup_log_backup_id_seq;
DROP TABLE IF EXISTS public.backup_log;
DROP SEQUENCE IF EXISTS public.audit_trail_log_id_seq;
DROP TABLE IF EXISTS public.audit_trail;
DROP SEQUENCE IF EXISTS public.analytics_cache_cache_id_seq;
DROP TABLE IF EXISTS public.analytics_cache;
DROP SEQUENCE IF EXISTS public.accession_log_accession_id_seq;
DROP TABLE IF EXISTS public.accession_log;
SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: accession_log; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.accession_log (
    accession_id integer NOT NULL,
    accession_number character varying(30) NOT NULL,
    book_id integer NOT NULL,
    librarian_id integer NOT NULL,
    date_accessioned date DEFAULT CURRENT_DATE NOT NULL,
    source character varying(20),
    updated_at timestamp without time zone,
    updated_by integer,
    CONSTRAINT accession_log_source_check CHECK (((source)::text = ANY ((ARRAY['purchase'::character varying, 'donation'::character varying, 'others'::character varying])::text[])))
);


ALTER TABLE public.accession_log OWNER TO postgres;

--
-- Name: accession_log_accession_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.accession_log_accession_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.accession_log_accession_id_seq OWNER TO postgres;

--
-- Name: accession_log_accession_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.accession_log_accession_id_seq OWNED BY public.accession_log.accession_id;


--
-- Name: analytics_cache; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.analytics_cache (
    cache_id integer NOT NULL,
    report_type character varying(40) NOT NULL,
    filter_params jsonb,
    kpi_data jsonb NOT NULL,
    generated_by integer,
    generated_date timestamp without time zone DEFAULT now() NOT NULL,
    CONSTRAINT analytics_cache_report_type_check CHECK (((report_type)::text = ANY ((ARRAY['books_borrowed_per_program'::character varying, 'utilization_rate'::character varying, 'most_borrowed_titles'::character varying, 'underutilized_titles'::character varying, 'online_resource_usage'::character varying, 'trend_borrowings'::character varying, 'trend_overdue'::character varying, 'top_categories'::character varying, 'top_books'::character varying, 'high_demand'::character varying, 'by_user_type'::character varying, 'collection_by_category'::character varying, 'copies_by_status'::character varying, 'recent_circulation'::character varying, 'recent_collection'::character varying, 'circulation_summary'::character varying])::text[])))
);


ALTER TABLE public.analytics_cache OWNER TO postgres;

--
-- Name: analytics_cache_cache_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.analytics_cache_cache_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.analytics_cache_cache_id_seq OWNER TO postgres;

--
-- Name: analytics_cache_cache_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.analytics_cache_cache_id_seq OWNED BY public.analytics_cache.cache_id;


--
-- Name: audit_trail; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.audit_trail (
    log_id integer NOT NULL,
    user_id integer,
    activity character varying(255) NOT NULL,
    session_token character varying(255),
    log_timestamp timestamp without time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.audit_trail OWNER TO postgres;

--
-- Name: audit_trail_log_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.audit_trail_log_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.audit_trail_log_id_seq OWNER TO postgres;

--
-- Name: audit_trail_log_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.audit_trail_log_id_seq OWNED BY public.audit_trail.log_id;


--
-- Name: backup_log; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.backup_log (
    backup_id integer NOT NULL,
    filename character varying(255) NOT NULL,
    size_bytes bigint,
    status character varying(20) DEFAULT 'completed'::character varying NOT NULL,
    backup_type character varying(20) DEFAULT 'manual'::character varying NOT NULL,
    error_msg character varying(500),
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    CONSTRAINT backup_log_backup_type_check CHECK (((backup_type)::text = ANY ((ARRAY['manual'::character varying, 'scheduled'::character varying])::text[]))),
    CONSTRAINT backup_log_status_check CHECK (((status)::text = ANY ((ARRAY['completed'::character varying, 'failed'::character varying, 'in_progress'::character varying])::text[])))
);


ALTER TABLE public.backup_log OWNER TO postgres;

--
-- Name: backup_log_backup_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.backup_log_backup_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.backup_log_backup_id_seq OWNER TO postgres;

--
-- Name: backup_log_backup_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.backup_log_backup_id_seq OWNED BY public.backup_log.backup_id;


--
-- Name: book_catalog; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.book_catalog (
    book_id integer NOT NULL,
    title character varying(255) NOT NULL,
    author character varying(150) NOT NULL,
    edition character varying(30),
    publisher character varying(150),
    year_published integer,
    subject_classification character varying(100),
    call_number character varying(50),
    isbn character varying(20),
    material_type character varying(30) DEFAULT 'Book'::character varying NOT NULL,
    description text,
    catalog_status character varying(20) DEFAULT 'active'::character varying NOT NULL,
    date_added date DEFAULT CURRENT_DATE NOT NULL,
    updated_at timestamp without time zone,
    updated_by integer,
    CONSTRAINT book_catalog_catalog_status_check CHECK (((catalog_status)::text = ANY ((ARRAY['active'::character varying, 'archived'::character varying])::text[])))
);


ALTER TABLE public.book_catalog OWNER TO postgres;

--
-- Name: book_catalog_book_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.book_catalog_book_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.book_catalog_book_id_seq OWNER TO postgres;

--
-- Name: book_catalog_book_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.book_catalog_book_id_seq OWNED BY public.book_catalog.book_id;


--
-- Name: borrowers; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.borrowers (
    borrower_id integer NOT NULL,
    user_id integer NOT NULL,
    id_number character varying(30) NOT NULL,
    department character varying(100),
    phone_number character varying(30),
    borrower_status character varying(20) DEFAULT 'active'::character varying NOT NULL,
    updated_at timestamp without time zone,
    updated_by integer,
    CONSTRAINT borrowers_borrower_status_check CHECK (((borrower_status)::text = ANY ((ARRAY['active'::character varying, 'blocked'::character varying])::text[])))
);


ALTER TABLE public.borrowers OWNER TO postgres;

--
-- Name: borrowers_borrower_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.borrowers_borrower_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.borrowers_borrower_id_seq OWNER TO postgres;

--
-- Name: borrowers_borrower_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.borrowers_borrower_id_seq OWNED BY public.borrowers.borrower_id;


--
-- Name: circulation_records; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.circulation_records (
    circulation_id integer NOT NULL,
    book_id integer NOT NULL,
    accession_id integer NOT NULL,
    borrower_id integer NOT NULL,
    processed_by integer NOT NULL,
    borrow_type character varying(30) NOT NULL,
    transaction_type character varying(20) NOT NULL,
    borrow_date date NOT NULL,
    due_date timestamp without time zone,
    return_date date,
    fine_amount numeric(8,2) DEFAULT 0.00 NOT NULL,
    fine_paid boolean DEFAULT false NOT NULL,
    damage_notes text,
    lost_flag boolean DEFAULT false NOT NULL,
    transaction_status character varying(20) NOT NULL,
    updated_at timestamp without time zone,
    updated_by integer,
    CONSTRAINT circulation_records_borrow_type_check CHECK (((borrow_type)::text = ANY ((ARRAY['overnight'::character varying, 'daily_circulation'::character varying])::text[]))),
    CONSTRAINT circulation_records_transaction_status_check CHECK (((transaction_status)::text = ANY ((ARRAY['active'::character varying, 'returned'::character varying, 'overdue'::character varying])::text[]))),
    CONSTRAINT circulation_records_transaction_type_check CHECK (((transaction_type)::text = ANY ((ARRAY['borrow'::character varying, 'return'::character varying])::text[])))
);


ALTER TABLE public.circulation_records OWNER TO postgres;

--
-- Name: circulation_records_circulation_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.circulation_records_circulation_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.circulation_records_circulation_id_seq OWNER TO postgres;

--
-- Name: circulation_records_circulation_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.circulation_records_circulation_id_seq OWNED BY public.circulation_records.circulation_id;


--
-- Name: departments; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.departments (
    department_id integer NOT NULL,
    name character varying(100) NOT NULL,
    dept_type character varying(20) NOT NULL,
    status character varying(20) DEFAULT 'active'::character varying NOT NULL,
    CONSTRAINT departments_dept_type_check CHECK (((dept_type)::text = ANY ((ARRAY['program'::character varying, 'department'::character varying])::text[]))),
    CONSTRAINT departments_status_check CHECK (((status)::text = ANY ((ARRAY['active'::character varying, 'inactive'::character varying])::text[])))
);


ALTER TABLE public.departments OWNER TO postgres;

--
-- Name: departments_department_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.departments_department_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.departments_department_id_seq OWNER TO postgres;

--
-- Name: departments_department_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.departments_department_id_seq OWNED BY public.departments.department_id;


--
-- Name: inventory_sessions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.inventory_sessions (
    session_id integer NOT NULL,
    librarian_id integer NOT NULL,
    total_books integer NOT NULL,
    scanned_count integer DEFAULT 0 NOT NULL,
    session_status character varying(20) DEFAULT 'active'::character varying NOT NULL,
    started_at timestamp without time zone DEFAULT now() NOT NULL,
    ended_at timestamp without time zone,
    updated_at timestamp without time zone,
    updated_by integer,
    CONSTRAINT inventory_sessions_session_status_check CHECK (((session_status)::text = ANY ((ARRAY['active'::character varying, 'completed'::character varying, 'cancelled'::character varying])::text[])))
);


ALTER TABLE public.inventory_sessions OWNER TO postgres;

--
-- Name: inventory_sessions_session_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.inventory_sessions_session_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.inventory_sessions_session_id_seq OWNER TO postgres;

--
-- Name: inventory_sessions_session_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.inventory_sessions_session_id_seq OWNED BY public.inventory_sessions.session_id;


--
-- Name: inventory_status; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.inventory_status (
    inventory_id integer NOT NULL,
    accession_id integer NOT NULL,
    inventory_state character varying(20) NOT NULL,
    inventory_type character varying(20) NOT NULL,
    checked_by integer,
    last_checked_date date NOT NULL,
    session_id integer,
    notes character varying(255),
    CONSTRAINT inventory_status_inventory_state_check CHECK (((inventory_state)::text = ANY ((ARRAY['available'::character varying, 'borrowed'::character varying, 'lost'::character varying, 'damaged'::character varying, 'missing'::character varying])::text[]))),
    CONSTRAINT inventory_status_inventory_type_check CHECK (((inventory_type)::text = ANY ((ARRAY['realtime_scan'::character varying, 'annual_physical'::character varying])::text[])))
);


ALTER TABLE public.inventory_status OWNER TO postgres;

--
-- Name: inventory_status_inventory_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.inventory_status_inventory_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.inventory_status_inventory_id_seq OWNER TO postgres;

--
-- Name: inventory_status_inventory_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.inventory_status_inventory_id_seq OWNED BY public.inventory_status.inventory_id;


--
-- Name: library_settings; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.library_settings (
    setting_key character varying(60) NOT NULL,
    setting_value text NOT NULL,
    description character varying(255),
    updated_at timestamp without time zone DEFAULT now() NOT NULL,
    updated_by integer
);


ALTER TABLE public.library_settings OWNER TO postgres;

--
-- Name: notification_log; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.notification_log (
    notification_id integer NOT NULL,
    recipient_id integer NOT NULL,
    message character varying(500) NOT NULL,
    notif_type character varying(30) NOT NULL,
    related_reference character varying(50),
    is_read boolean DEFAULT false NOT NULL,
    date_sent timestamp without time zone DEFAULT now() NOT NULL,
    updated_at timestamp without time zone,
    updated_by integer,
    CONSTRAINT notification_log_notif_type_check CHECK (((notif_type)::text = ANY ((ARRAY['status_update'::character varying, 'hold_ready'::character varying, 'overdue_reminder'::character varying, 'borrow'::character varying, 'return'::character varying, 'request_update'::character varying, 'fine'::character varying, 'due_soon'::character varying, 'reservation'::character varying])::text[])))
);


ALTER TABLE public.notification_log OWNER TO postgres;

--
-- Name: notification_log_notification_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.notification_log_notification_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.notification_log_notification_id_seq OWNER TO postgres;

--
-- Name: notification_log_notification_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.notification_log_notification_id_seq OWNED BY public.notification_log.notification_id;


--
-- Name: procurement_log; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.procurement_log (
    procurement_id integer NOT NULL,
    request_id integer NOT NULL,
    order_status character varying(30) NOT NULL,
    order_date date NOT NULL,
    date_received date,
    book_id integer,
    remarks character varying(255),
    updated_at timestamp without time zone,
    updated_by integer,
    CONSTRAINT procurement_log_order_status_check CHECK (((order_status)::text = ANY ((ARRAY['for_ordering'::character varying, 'ordered'::character varying, 'delivered'::character varying, 'cancelled'::character varying, 'out_of_stock'::character varying, 'procured'::character varying])::text[])))
);


ALTER TABLE public.procurement_log OWNER TO postgres;

--
-- Name: procurement_log_procurement_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.procurement_log_procurement_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.procurement_log_procurement_id_seq OWNER TO postgres;

--
-- Name: procurement_log_procurement_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.procurement_log_procurement_id_seq OWNED BY public.procurement_log.procurement_id;


--
-- Name: request_records; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.request_records (
    request_id integer NOT NULL,
    requester_id integer NOT NULL,
    book_title character varying(255) NOT NULL,
    author character varying(150),
    matched_book_id integer,
    request_status character varying(30) DEFAULT 'pending_review'::character varying NOT NULL,
    request_date timestamp without time zone DEFAULT now() NOT NULL,
    reviewed_by integer,
    review_date timestamp without time zone,
    remarks character varying(255),
    updated_at timestamp without time zone,
    updated_by integer,
    CONSTRAINT request_records_request_status_check CHECK (((request_status)::text = ANY ((ARRAY['pending_review'::character varying, 'existing_in_collection'::character varying, 'approved'::character varying, 'rejected'::character varying, 'procured'::character varying])::text[])))
);


ALTER TABLE public.request_records OWNER TO postgres;

--
-- Name: request_records_request_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.request_records_request_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.request_records_request_id_seq OWNER TO postgres;

--
-- Name: request_records_request_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.request_records_request_id_seq OWNED BY public.request_records.request_id;


--
-- Name: reservation_queue; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.reservation_queue (
    reservation_id integer NOT NULL,
    book_id integer NOT NULL,
    borrower_id integer NOT NULL,
    queue_position integer NOT NULL,
    request_date timestamp without time zone DEFAULT now() NOT NULL,
    reservation_status character varying(20) NOT NULL,
    claim_deadline timestamp without time zone,
    updated_at timestamp without time zone,
    updated_by integer,
    CONSTRAINT reservation_queue_reservation_status_check CHECK (((reservation_status)::text = ANY ((ARRAY['waiting'::character varying, 'allocated'::character varying, 'claimed'::character varying, 'expired'::character varying])::text[])))
);


ALTER TABLE public.reservation_queue OWNER TO postgres;

--
-- Name: reservation_queue_reservation_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.reservation_queue_reservation_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.reservation_queue_reservation_id_seq OWNER TO postgres;

--
-- Name: reservation_queue_reservation_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.reservation_queue_reservation_id_seq OWNED BY public.reservation_queue.reservation_id;


--
-- Name: roles; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.roles (
    role_id integer NOT NULL,
    role_name character varying(50) NOT NULL,
    permissions jsonb
);


ALTER TABLE public.roles OWNER TO postgres;

--
-- Name: roles_role_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.roles_role_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.roles_role_id_seq OWNER TO postgres;

--
-- Name: roles_role_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.roles_role_id_seq OWNED BY public.roles.role_id;


--
-- Name: user_accounts; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.user_accounts (
    user_id integer NOT NULL,
    email character varying(100) NOT NULL,
    oauth_sub character varying(255) NOT NULL,
    full_name character varying(150) NOT NULL,
    role_id integer NOT NULL,
    account_status character varying(20) DEFAULT 'active'::character varying NOT NULL,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    updated_at timestamp without time zone,
    updated_by integer,
    CONSTRAINT user_accounts_account_status_check CHECK (((account_status)::text = ANY ((ARRAY['active'::character varying, 'disabled'::character varying, 'pending'::character varying, 'archived'::character varying])::text[])))
);


ALTER TABLE public.user_accounts OWNER TO postgres;

--
-- Name: user_accounts_user_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.user_accounts_user_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.user_accounts_user_id_seq OWNER TO postgres;

--
-- Name: user_accounts_user_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.user_accounts_user_id_seq OWNED BY public.user_accounts.user_id;


--
-- Name: user_favorites; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.user_favorites (
    favorite_id integer NOT NULL,
    user_id integer NOT NULL,
    book_id integer NOT NULL,
    created_at timestamp without time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.user_favorites OWNER TO postgres;

--
-- Name: user_favorites_favorite_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.user_favorites_favorite_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.user_favorites_favorite_id_seq OWNER TO postgres;

--
-- Name: user_favorites_favorite_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.user_favorites_favorite_id_seq OWNED BY public.user_favorites.favorite_id;


--
-- Name: accession_log accession_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.accession_log ALTER COLUMN accession_id SET DEFAULT nextval('public.accession_log_accession_id_seq'::regclass);


--
-- Name: analytics_cache cache_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.analytics_cache ALTER COLUMN cache_id SET DEFAULT nextval('public.analytics_cache_cache_id_seq'::regclass);


--
-- Name: audit_trail log_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.audit_trail ALTER COLUMN log_id SET DEFAULT nextval('public.audit_trail_log_id_seq'::regclass);


--
-- Name: backup_log backup_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.backup_log ALTER COLUMN backup_id SET DEFAULT nextval('public.backup_log_backup_id_seq'::regclass);


--
-- Name: book_catalog book_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.book_catalog ALTER COLUMN book_id SET DEFAULT nextval('public.book_catalog_book_id_seq'::regclass);


--
-- Name: borrowers borrower_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.borrowers ALTER COLUMN borrower_id SET DEFAULT nextval('public.borrowers_borrower_id_seq'::regclass);


--
-- Name: circulation_records circulation_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.circulation_records ALTER COLUMN circulation_id SET DEFAULT nextval('public.circulation_records_circulation_id_seq'::regclass);


--
-- Name: departments department_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.departments ALTER COLUMN department_id SET DEFAULT nextval('public.departments_department_id_seq'::regclass);


--
-- Name: inventory_sessions session_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.inventory_sessions ALTER COLUMN session_id SET DEFAULT nextval('public.inventory_sessions_session_id_seq'::regclass);


--
-- Name: inventory_status inventory_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.inventory_status ALTER COLUMN inventory_id SET DEFAULT nextval('public.inventory_status_inventory_id_seq'::regclass);


--
-- Name: notification_log notification_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.notification_log ALTER COLUMN notification_id SET DEFAULT nextval('public.notification_log_notification_id_seq'::regclass);


--
-- Name: procurement_log procurement_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.procurement_log ALTER COLUMN procurement_id SET DEFAULT nextval('public.procurement_log_procurement_id_seq'::regclass);


--
-- Name: request_records request_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.request_records ALTER COLUMN request_id SET DEFAULT nextval('public.request_records_request_id_seq'::regclass);


--
-- Name: reservation_queue reservation_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.reservation_queue ALTER COLUMN reservation_id SET DEFAULT nextval('public.reservation_queue_reservation_id_seq'::regclass);


--
-- Name: roles role_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.roles ALTER COLUMN role_id SET DEFAULT nextval('public.roles_role_id_seq'::regclass);


--
-- Name: user_accounts user_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_accounts ALTER COLUMN user_id SET DEFAULT nextval('public.user_accounts_user_id_seq'::regclass);


--
-- Name: user_favorites favorite_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_favorites ALTER COLUMN favorite_id SET DEFAULT nextval('public.user_favorites_favorite_id_seq'::regclass);


--
-- Data for Name: accession_log; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.accession_log (accession_id, accession_number, book_id, librarian_id, date_accessioned, source, updated_at, updated_by) FROM stdin;
1	0001	1	1	2026-10-08	donation	\N	\N
2	0002	1	1	2026-10-08	purchase	\N	\N
3	0003	1	1	2026-10-08	purchase	\N	\N
4	0004	1	1	2026-10-08	purchase	\N	\N
5	0005	1	1	2026-10-08	purchase	\N	\N
6	0006	1	1	2026-10-08	purchase	\N	\N
7	0007	1	1	2026-10-08	purchase	\N	\N
8	0008	1	1	2026-10-08	donation	\N	\N
9	0009	1	1	2026-10-08	purchase	\N	\N
10	0010	1	1	2026-10-08	purchase	\N	\N
11	0011	1	1	2026-10-08	purchase	\N	\N
12	0012	1	1	2026-10-08	purchase	\N	\N
13	0013	1	1	2026-10-08	purchase	\N	\N
14	0014	1	1	2026-10-08	purchase	\N	\N
15	0015	1	1	2026-10-08	donation	\N	\N
16	0016	1	1	2026-10-08	purchase	\N	\N
17	0017	1	1	2026-10-08	purchase	\N	\N
18	0018	1	1	2026-10-08	purchase	\N	\N
19	0019	1	1	2026-10-08	purchase	\N	\N
20	0020	1	1	2026-10-08	purchase	\N	\N
21	0021	1	1	2026-10-08	purchase	\N	\N
22	0022	1	1	2026-10-08	donation	\N	\N
23	0023	1	1	2026-10-08	purchase	\N	\N
24	0024	1	1	2026-10-08	purchase	\N	\N
25	0025	2	1	2026-10-08	purchase	\N	\N
26	0026	2	1	2026-10-08	purchase	\N	\N
27	0027	2	1	2026-10-08	purchase	\N	\N
28	0028	2	1	2026-10-08	purchase	\N	\N
29	0029	2	1	2026-10-08	purchase	\N	\N
30	0030	2	1	2026-10-08	purchase	\N	\N
31	0031	2	1	2026-10-08	donation	\N	\N
32	0032	2	1	2026-10-08	purchase	\N	\N
33	0033	2	1	2026-10-08	purchase	\N	\N
34	0034	2	1	2026-10-08	purchase	\N	\N
35	0035	2	1	2026-10-08	purchase	\N	\N
36	0036	2	1	2026-10-08	purchase	\N	\N
37	0037	2	1	2026-10-08	purchase	\N	\N
38	0038	2	1	2026-10-08	donation	\N	\N
39	0039	2	1	2026-10-08	purchase	\N	\N
40	0040	2	1	2026-10-08	purchase	\N	\N
41	0041	3	1	2026-10-08	purchase	\N	\N
42	0042	3	1	2026-10-08	purchase	\N	\N
43	0043	3	1	2026-10-08	purchase	\N	\N
44	0044	3	1	2026-10-08	purchase	\N	\N
45	0045	3	1	2026-10-08	purchase	\N	\N
46	0046	3	1	2026-10-08	donation	\N	\N
47	0047	3	1	2026-10-08	purchase	\N	\N
48	0048	3	1	2026-10-08	purchase	\N	\N
49	0049	3	1	2026-10-08	purchase	\N	\N
50	0050	3	1	2026-10-08	purchase	\N	\N
51	0051	3	1	2026-10-08	purchase	\N	\N
52	0052	3	1	2026-10-08	purchase	\N	\N
53	0053	3	1	2026-10-08	donation	\N	\N
54	0054	3	1	2026-10-08	purchase	\N	\N
55	0055	3	1	2026-10-08	purchase	\N	\N
56	0056	3	1	2026-10-08	purchase	\N	\N
57	0057	3	1	2026-10-08	purchase	\N	\N
58	0058	3	1	2026-10-08	purchase	\N	\N
59	0059	3	1	2026-10-08	purchase	\N	\N
60	0060	3	1	2026-10-08	donation	\N	\N
61	0061	3	1	2026-10-08	purchase	\N	\N
62	0062	3	1	2026-10-08	purchase	\N	\N
63	0063	4	1	2026-10-08	purchase	\N	\N
64	0064	4	1	2026-10-08	purchase	\N	\N
65	0065	4	1	2026-10-08	purchase	\N	\N
66	0066	4	1	2026-10-08	purchase	\N	\N
67	0067	4	1	2026-10-08	donation	\N	\N
68	0068	4	1	2026-10-08	purchase	\N	\N
69	0069	4	1	2026-10-08	purchase	\N	\N
70	0070	4	1	2026-10-08	purchase	\N	\N
71	0071	4	1	2026-10-08	purchase	\N	\N
72	0072	4	1	2026-10-08	purchase	\N	\N
73	0073	4	1	2026-10-08	purchase	\N	\N
74	0074	4	1	2026-10-08	donation	\N	\N
75	0075	4	1	2026-10-08	purchase	\N	\N
76	0076	4	1	2026-10-08	purchase	\N	\N
77	0077	4	1	2026-10-08	purchase	\N	\N
78	0078	4	1	2026-10-08	purchase	\N	\N
79	0079	4	1	2026-10-08	purchase	\N	\N
80	0080	4	1	2026-10-08	purchase	\N	\N
81	0081	4	1	2026-10-08	donation	\N	\N
82	0082	5	1	2026-10-08	purchase	\N	\N
83	0083	5	1	2026-10-08	purchase	\N	\N
84	0084	5	1	2026-10-08	purchase	\N	\N
85	0085	5	1	2026-10-08	donation	\N	\N
86	0086	5	1	2026-10-08	purchase	\N	\N
87	0087	5	1	2026-10-08	purchase	\N	\N
88	0088	5	1	2026-10-08	purchase	\N	\N
89	0089	5	1	2026-10-08	purchase	\N	\N
90	0090	5	1	2026-10-08	purchase	\N	\N
91	0091	5	1	2026-10-08	purchase	\N	\N
92	0092	5	1	2026-10-08	donation	\N	\N
93	0093	5	1	2026-10-08	purchase	\N	\N
94	0094	5	1	2026-10-08	purchase	\N	\N
95	0095	5	1	2026-10-08	purchase	\N	\N
96	0096	5	1	2026-10-08	purchase	\N	\N
97	0097	5	1	2026-10-08	purchase	\N	\N
98	0098	5	1	2026-10-08	purchase	\N	\N
99	0099	5	1	2026-10-08	donation	\N	\N
100	0100	5	1	2026-10-08	purchase	\N	\N
101	0101	5	1	2026-10-08	purchase	\N	\N
102	0102	5	1	2026-10-08	purchase	\N	\N
103	0103	5	1	2026-10-08	purchase	\N	\N
104	0104	6	1	2026-10-08	purchase	\N	\N
105	0105	6	1	2026-10-08	purchase	\N	\N
106	0106	6	1	2026-10-08	donation	\N	\N
107	0107	6	1	2026-10-08	purchase	\N	\N
108	0108	6	1	2026-10-08	purchase	\N	\N
109	0109	6	1	2026-10-08	purchase	\N	\N
110	0110	6	1	2026-10-08	purchase	\N	\N
111	0111	6	1	2026-10-08	purchase	\N	\N
112	0112	6	1	2026-10-08	purchase	\N	\N
113	0113	6	1	2026-10-08	donation	\N	\N
114	0114	6	1	2026-10-08	purchase	\N	\N
115	0115	6	1	2026-10-08	purchase	\N	\N
116	0116	6	1	2026-10-08	purchase	\N	\N
117	0117	6	1	2026-10-08	purchase	\N	\N
118	0118	6	1	2026-10-08	purchase	\N	\N
119	0119	6	1	2026-10-08	purchase	\N	\N
120	0120	6	1	2026-10-08	donation	\N	\N
121	0121	6	1	2026-10-08	purchase	\N	\N
122	0122	6	1	2026-10-08	purchase	\N	\N
123	0123	7	1	2026-10-08	purchase	\N	\N
124	0124	7	1	2026-10-08	donation	\N	\N
125	0125	7	1	2026-10-08	purchase	\N	\N
126	0126	7	1	2026-10-08	purchase	\N	\N
127	0127	7	1	2026-10-08	purchase	\N	\N
128	0128	7	1	2026-10-08	purchase	\N	\N
129	0129	7	1	2026-10-08	purchase	\N	\N
130	0130	7	1	2026-10-08	purchase	\N	\N
131	0131	7	1	2026-10-08	donation	\N	\N
132	0132	7	1	2026-10-08	purchase	\N	\N
133	0133	7	1	2026-10-08	purchase	\N	\N
134	0134	7	1	2026-10-08	purchase	\N	\N
135	0135	7	1	2026-10-08	purchase	\N	\N
136	0136	7	1	2026-10-08	purchase	\N	\N
137	0137	7	1	2026-10-08	purchase	\N	\N
138	0138	7	1	2026-10-08	donation	\N	\N
139	0139	8	1	2026-10-08	donation	\N	\N
140	0140	8	1	2026-10-08	purchase	\N	\N
141	0141	8	1	2026-10-08	purchase	\N	\N
142	0142	8	1	2026-10-08	purchase	\N	\N
143	0143	8	1	2026-10-08	purchase	\N	\N
144	0144	8	1	2026-10-08	purchase	\N	\N
145	0145	8	1	2026-10-08	purchase	\N	\N
146	0146	8	1	2026-10-08	donation	\N	\N
147	0147	8	1	2026-10-08	purchase	\N	\N
148	0148	8	1	2026-10-08	purchase	\N	\N
149	0149	8	1	2026-10-08	purchase	\N	\N
150	0150	8	1	2026-10-08	purchase	\N	\N
151	0151	8	1	2026-10-08	purchase	\N	\N
152	0152	8	1	2026-10-08	purchase	\N	\N
153	0153	8	1	2026-10-08	donation	\N	\N
154	0154	8	1	2026-10-08	purchase	\N	\N
155	0155	8	1	2026-10-08	purchase	\N	\N
156	0156	8	1	2026-10-08	purchase	\N	\N
157	0157	8	1	2026-10-08	purchase	\N	\N
158	0158	8	1	2026-10-08	purchase	\N	\N
159	0159	9	1	2026-10-08	purchase	\N	\N
160	0160	9	1	2026-10-08	purchase	\N	\N
161	0161	9	1	2026-10-08	purchase	\N	\N
162	0162	9	1	2026-10-08	purchase	\N	\N
163	0163	9	1	2026-10-08	purchase	\N	\N
164	0164	9	1	2026-10-08	purchase	\N	\N
165	0165	9	1	2026-10-08	donation	\N	\N
166	0166	9	1	2026-10-08	purchase	\N	\N
167	0167	9	1	2026-10-08	purchase	\N	\N
168	0168	9	1	2026-10-08	purchase	\N	\N
169	0169	9	1	2026-10-08	purchase	\N	\N
170	0170	9	1	2026-10-08	purchase	\N	\N
171	0171	9	1	2026-10-08	purchase	\N	\N
172	0172	9	1	2026-10-08	donation	\N	\N
173	0173	9	1	2026-10-08	purchase	\N	\N
174	0174	9	1	2026-10-08	purchase	\N	\N
175	0175	9	1	2026-10-08	purchase	\N	\N
176	0176	9	1	2026-10-08	purchase	\N	\N
177	0177	10	1	2026-10-08	purchase	\N	\N
178	0178	10	1	2026-10-08	purchase	\N	\N
179	0179	10	1	2026-10-08	purchase	\N	\N
180	0180	10	1	2026-10-08	purchase	\N	\N
181	0181	10	1	2026-10-08	purchase	\N	\N
182	0182	10	1	2026-10-08	donation	\N	\N
183	0183	10	1	2026-10-08	purchase	\N	\N
184	0184	10	1	2026-10-08	purchase	\N	\N
185	0185	10	1	2026-10-08	purchase	\N	\N
186	0186	10	1	2026-10-08	purchase	\N	\N
187	0187	10	1	2026-10-08	purchase	\N	\N
188	0188	10	1	2026-10-08	purchase	\N	\N
189	0189	10	1	2026-10-08	donation	\N	\N
190	0190	10	1	2026-10-08	purchase	\N	\N
191	0191	10	1	2026-10-08	purchase	\N	\N
192	0192	10	1	2026-10-08	purchase	\N	\N
193	0193	11	1	2026-10-08	purchase	\N	\N
194	0194	11	1	2026-10-08	purchase	\N	\N
195	0195	11	1	2026-10-08	purchase	\N	\N
196	0196	11	1	2026-10-08	purchase	\N	\N
197	0197	11	1	2026-10-08	donation	\N	\N
198	0198	11	1	2026-10-08	purchase	\N	\N
199	0199	11	1	2026-10-08	purchase	\N	\N
200	0200	11	1	2026-10-08	purchase	\N	\N
201	0201	11	1	2026-10-08	purchase	\N	\N
202	0202	11	1	2026-10-08	purchase	\N	\N
203	0203	11	1	2026-10-08	purchase	\N	\N
204	0204	11	1	2026-10-08	donation	\N	\N
205	0205	11	1	2026-10-08	purchase	\N	\N
206	0206	11	1	2026-10-08	purchase	\N	\N
207	0207	11	1	2026-10-08	purchase	\N	\N
208	0208	11	1	2026-10-08	purchase	\N	\N
209	0209	12	1	2026-10-08	purchase	\N	\N
210	0210	12	1	2026-10-08	purchase	\N	\N
211	0211	12	1	2026-10-08	purchase	\N	\N
212	0212	12	1	2026-10-08	donation	\N	\N
213	0213	12	1	2026-10-08	purchase	\N	\N
214	0214	12	1	2026-10-08	purchase	\N	\N
215	0215	12	1	2026-10-08	purchase	\N	\N
216	0216	12	1	2026-10-08	purchase	\N	\N
217	0217	12	1	2026-10-08	purchase	\N	\N
218	0218	12	1	2026-10-08	purchase	\N	\N
219	0219	12	1	2026-10-08	donation	\N	\N
220	0220	12	1	2026-10-08	purchase	\N	\N
221	0221	13	1	2026-10-08	purchase	\N	\N
222	0222	13	1	2026-10-08	purchase	\N	\N
223	0223	13	1	2026-10-08	donation	\N	\N
224	0224	13	1	2026-10-08	purchase	\N	\N
225	0225	13	1	2026-10-08	purchase	\N	\N
226	0226	13	1	2026-10-08	purchase	\N	\N
227	0227	13	1	2026-10-08	purchase	\N	\N
228	0228	13	1	2026-10-08	purchase	\N	\N
229	0229	13	1	2026-10-08	purchase	\N	\N
230	0230	13	1	2026-10-08	donation	\N	\N
231	0231	13	1	2026-10-08	purchase	\N	\N
232	0232	13	1	2026-10-08	purchase	\N	\N
233	0233	13	1	2026-10-08	purchase	\N	\N
234	0234	13	1	2026-10-08	purchase	\N	\N
235	0235	13	1	2026-10-08	purchase	\N	\N
236	0236	13	1	2026-10-08	purchase	\N	\N
237	0237	13	1	2026-10-08	donation	\N	\N
238	0238	13	1	2026-10-08	purchase	\N	\N
239	0239	14	1	2026-10-08	purchase	\N	\N
240	0240	14	1	2026-10-08	donation	\N	\N
241	0241	14	1	2026-10-08	purchase	\N	\N
242	0242	14	1	2026-10-08	purchase	\N	\N
243	0243	14	1	2026-10-08	purchase	\N	\N
244	0244	14	1	2026-10-08	purchase	\N	\N
245	0245	14	1	2026-10-08	purchase	\N	\N
246	0246	14	1	2026-10-08	purchase	\N	\N
247	0247	14	1	2026-10-08	donation	\N	\N
248	0248	14	1	2026-10-08	purchase	\N	\N
249	0249	14	1	2026-10-08	purchase	\N	\N
250	0250	14	1	2026-10-08	purchase	\N	\N
251	0251	15	1	2026-10-08	donation	\N	\N
252	0252	15	1	2026-10-08	purchase	\N	\N
253	0253	15	1	2026-10-08	purchase	\N	\N
254	0254	15	1	2026-10-08	purchase	\N	\N
255	0255	15	1	2026-10-08	purchase	\N	\N
256	0256	15	1	2026-10-08	purchase	\N	\N
257	0257	15	1	2026-10-08	purchase	\N	\N
258	0258	15	1	2026-10-08	donation	\N	\N
259	0259	15	1	2026-10-08	purchase	\N	\N
260	0260	15	1	2026-10-08	purchase	\N	\N
261	0261	16	1	2026-10-08	purchase	\N	\N
262	0262	16	1	2026-10-08	purchase	\N	\N
263	0263	16	1	2026-10-08	purchase	\N	\N
264	0264	16	1	2026-10-08	purchase	\N	\N
265	0265	16	1	2026-10-08	purchase	\N	\N
266	0266	16	1	2026-10-08	purchase	\N	\N
267	0267	16	1	2026-10-08	donation	\N	\N
268	0268	16	1	2026-10-08	purchase	\N	\N
269	0269	16	1	2026-10-08	purchase	\N	\N
270	0270	16	1	2026-10-08	purchase	\N	\N
271	0271	16	1	2026-10-08	purchase	\N	\N
272	0272	16	1	2026-10-08	purchase	\N	\N
273	0273	17	1	2026-10-08	purchase	\N	\N
274	0274	17	1	2026-10-08	purchase	\N	\N
275	0275	17	1	2026-10-08	purchase	\N	\N
276	0276	17	1	2026-10-08	purchase	\N	\N
277	0277	17	1	2026-10-08	purchase	\N	\N
278	0278	17	1	2026-10-08	donation	\N	\N
279	0279	17	1	2026-10-08	purchase	\N	\N
280	0280	17	1	2026-10-08	purchase	\N	\N
281	0281	17	1	2026-10-08	purchase	\N	\N
282	0282	17	1	2026-10-08	purchase	\N	\N
283	0283	17	1	2026-10-08	purchase	\N	\N
284	0284	17	1	2026-10-08	purchase	\N	\N
285	0285	18	1	2026-10-08	purchase	\N	\N
286	0286	18	1	2026-10-08	purchase	\N	\N
287	0287	18	1	2026-10-08	purchase	\N	\N
288	0288	18	1	2026-10-08	purchase	\N	\N
289	0289	18	1	2026-10-08	donation	\N	\N
290	0290	18	1	2026-10-08	purchase	\N	\N
291	0291	18	1	2026-10-08	purchase	\N	\N
292	0292	18	1	2026-10-08	purchase	\N	\N
293	0293	18	1	2026-10-08	purchase	\N	\N
294	0294	19	1	2026-10-08	purchase	\N	\N
295	0295	19	1	2026-10-08	purchase	\N	\N
296	0296	19	1	2026-10-08	purchase	\N	\N
297	0297	19	1	2026-10-08	donation	\N	\N
298	0298	19	1	2026-10-08	purchase	\N	\N
299	0299	19	1	2026-10-08	purchase	\N	\N
300	0300	19	1	2026-10-08	purchase	\N	\N
301	0301	19	1	2026-10-08	purchase	\N	\N
302	0302	19	1	2026-10-08	purchase	\N	\N
303	0303	19	1	2026-10-08	purchase	\N	\N
304	0304	19	1	2026-10-08	donation	\N	\N
305	0305	19	1	2026-10-08	purchase	\N	\N
306	0306	19	1	2026-10-08	purchase	\N	\N
307	0307	19	1	2026-10-08	purchase	\N	\N
308	0308	19	1	2026-10-08	purchase	\N	\N
309	0309	19	1	2026-10-08	purchase	\N	\N
310	0310	19	1	2026-10-08	purchase	\N	\N
311	0311	19	1	2026-10-08	donation	\N	\N
312	0312	20	1	2026-10-08	purchase	\N	\N
313	0313	20	1	2026-10-08	purchase	\N	\N
314	0314	20	1	2026-10-08	donation	\N	\N
315	0315	20	1	2026-10-08	purchase	\N	\N
316	0316	20	1	2026-10-08	purchase	\N	\N
317	0317	20	1	2026-10-08	purchase	\N	\N
318	0318	20	1	2026-10-08	purchase	\N	\N
319	0319	20	1	2026-10-08	purchase	\N	\N
320	0320	20	1	2026-10-08	purchase	\N	\N
321	0321	20	1	2026-10-08	donation	\N	\N
322	0322	20	1	2026-10-08	purchase	\N	\N
323	0323	20	1	2026-10-08	purchase	\N	\N
324	0324	20	1	2026-10-08	purchase	\N	\N
325	0325	20	1	2026-10-08	purchase	\N	\N
326	0326	21	1	2026-10-08	purchase	\N	\N
327	0327	21	1	2026-10-08	donation	\N	\N
328	0328	21	1	2026-10-08	purchase	\N	\N
329	0329	21	1	2026-10-08	purchase	\N	\N
330	0330	21	1	2026-10-08	purchase	\N	\N
331	0331	21	1	2026-10-08	purchase	\N	\N
332	0332	21	1	2026-10-08	purchase	\N	\N
333	0333	21	1	2026-10-08	purchase	\N	\N
334	0334	21	1	2026-10-08	donation	\N	\N
335	0335	21	1	2026-10-08	purchase	\N	\N
336	0336	21	1	2026-10-08	purchase	\N	\N
337	0337	21	1	2026-10-08	purchase	\N	\N
338	0338	21	1	2026-10-08	purchase	\N	\N
339	0339	21	1	2026-10-08	purchase	\N	\N
340	0340	22	1	2026-10-08	donation	\N	\N
341	0341	22	1	2026-10-08	purchase	\N	\N
342	0342	22	1	2026-10-08	purchase	\N	\N
343	0343	22	1	2026-10-08	purchase	\N	\N
344	0344	22	1	2026-10-08	purchase	\N	\N
345	0345	22	1	2026-10-08	purchase	\N	\N
346	0346	22	1	2026-10-08	purchase	\N	\N
347	0347	22	1	2026-10-08	donation	\N	\N
348	0348	22	1	2026-10-08	purchase	\N	\N
349	0349	22	1	2026-10-08	purchase	\N	\N
350	0350	22	1	2026-10-08	purchase	\N	\N
351	0351	22	1	2026-10-08	purchase	\N	\N
352	0352	22	1	2026-10-08	purchase	\N	\N
353	0353	22	1	2026-10-08	purchase	\N	\N
354	0354	23	1	2026-10-08	purchase	\N	\N
355	0355	23	1	2026-10-08	purchase	\N	\N
356	0356	23	1	2026-10-08	purchase	\N	\N
357	0357	23	1	2026-10-08	purchase	\N	\N
358	0358	23	1	2026-10-08	purchase	\N	\N
359	0359	23	1	2026-10-08	purchase	\N	\N
360	0360	23	1	2026-10-08	donation	\N	\N
361	0361	23	1	2026-10-08	purchase	\N	\N
362	0362	23	1	2026-10-08	purchase	\N	\N
363	0363	23	1	2026-10-08	purchase	\N	\N
364	0364	23	1	2026-10-08	purchase	\N	\N
365	0365	23	1	2026-10-08	purchase	\N	\N
366	0366	24	1	2026-10-08	purchase	\N	\N
367	0367	24	1	2026-10-08	purchase	\N	\N
368	0368	24	1	2026-10-08	purchase	\N	\N
369	0369	24	1	2026-10-08	purchase	\N	\N
370	0370	24	1	2026-10-08	purchase	\N	\N
371	0371	24	1	2026-10-08	donation	\N	\N
372	0372	24	1	2026-10-08	purchase	\N	\N
373	0373	24	1	2026-10-08	purchase	\N	\N
374	0374	24	1	2026-10-08	purchase	\N	\N
375	0375	24	1	2026-10-08	purchase	\N	\N
376	0376	25	1	2026-10-08	purchase	\N	\N
377	0377	25	1	2026-10-08	purchase	\N	\N
378	0378	25	1	2026-10-08	purchase	\N	\N
379	0379	25	1	2026-10-08	purchase	\N	\N
380	0380	25	1	2026-10-08	donation	\N	\N
381	0381	25	1	2026-10-08	purchase	\N	\N
382	0382	25	1	2026-10-08	purchase	\N	\N
383	0383	25	1	2026-10-08	purchase	\N	\N
384	0384	25	1	2026-10-08	purchase	\N	\N
385	0385	25	1	2026-10-08	purchase	\N	\N
386	0386	26	1	2026-10-08	purchase	\N	\N
387	0387	26	1	2026-10-08	purchase	\N	\N
388	0388	26	1	2026-10-08	purchase	\N	\N
389	0389	26	1	2026-10-08	donation	\N	\N
390	0390	26	1	2026-10-08	purchase	\N	\N
391	0391	26	1	2026-10-08	purchase	\N	\N
392	0392	26	1	2026-10-08	purchase	\N	\N
393	0393	26	1	2026-10-08	purchase	\N	\N
394	0394	26	1	2026-10-08	purchase	\N	\N
395	0395	27	1	2026-10-08	purchase	\N	\N
396	0396	27	1	2026-10-08	purchase	\N	\N
397	0397	27	1	2026-10-08	donation	\N	\N
398	0398	27	1	2026-10-08	purchase	\N	\N
399	0399	27	1	2026-10-08	purchase	\N	\N
400	0400	27	1	2026-10-08	purchase	\N	\N
401	0401	27	1	2026-10-08	purchase	\N	\N
402	0402	27	1	2026-10-08	purchase	\N	\N
403	0403	27	1	2026-10-08	purchase	\N	\N
404	0404	27	1	2026-10-08	donation	\N	\N
405	0405	27	1	2026-10-08	purchase	\N	\N
406	0406	27	1	2026-10-08	purchase	\N	\N
407	0407	27	1	2026-10-08	purchase	\N	\N
408	0408	27	1	2026-10-08	purchase	\N	\N
409	0409	27	1	2026-10-08	purchase	\N	\N
410	0410	27	1	2026-10-08	purchase	\N	\N
411	0411	28	1	2026-10-08	purchase	\N	\N
412	0412	28	1	2026-10-08	donation	\N	\N
413	0413	28	1	2026-10-08	purchase	\N	\N
414	0414	28	1	2026-10-08	purchase	\N	\N
415	0415	28	1	2026-10-08	purchase	\N	\N
416	0416	28	1	2026-10-08	purchase	\N	\N
417	0417	28	1	2026-10-08	purchase	\N	\N
418	0418	28	1	2026-10-08	purchase	\N	\N
419	0419	28	1	2026-10-08	donation	\N	\N
420	0420	28	1	2026-10-08	purchase	\N	\N
421	0421	28	1	2026-10-08	purchase	\N	\N
422	0422	28	1	2026-10-08	purchase	\N	\N
423	0423	28	1	2026-10-08	purchase	\N	\N
424	0424	28	1	2026-10-08	purchase	\N	\N
425	0425	29	1	2026-10-08	donation	\N	\N
426	0426	29	1	2026-10-08	purchase	\N	\N
427	0427	29	1	2026-10-08	purchase	\N	\N
428	0428	29	1	2026-10-08	purchase	\N	\N
429	0429	29	1	2026-10-08	purchase	\N	\N
430	0430	29	1	2026-10-08	purchase	\N	\N
431	0431	29	1	2026-10-08	purchase	\N	\N
432	0432	29	1	2026-10-08	donation	\N	\N
433	0433	29	1	2026-10-08	purchase	\N	\N
434	0434	29	1	2026-10-08	purchase	\N	\N
435	0435	29	1	2026-10-08	purchase	\N	\N
436	0436	29	1	2026-10-08	purchase	\N	\N
437	0437	30	1	2026-10-08	purchase	\N	\N
438	0438	30	1	2026-10-08	purchase	\N	\N
439	0439	30	1	2026-10-08	purchase	\N	\N
440	0440	30	1	2026-10-08	purchase	\N	\N
441	0441	30	1	2026-10-08	purchase	\N	\N
442	0442	30	1	2026-10-08	purchase	\N	\N
443	0443	30	1	2026-10-08	donation	\N	\N
444	0444	30	1	2026-10-08	purchase	\N	\N
445	0445	30	1	2026-10-08	purchase	\N	\N
446	0446	30	1	2026-10-08	purchase	\N	\N
447	0447	31	1	2026-10-08	purchase	\N	\N
448	0448	31	1	2026-10-08	purchase	\N	\N
449	0449	31	1	2026-10-08	purchase	\N	\N
450	0450	31	1	2026-10-08	purchase	\N	\N
451	0451	31	1	2026-10-08	purchase	\N	\N
452	0452	31	1	2026-10-08	donation	\N	\N
453	0453	31	1	2026-10-08	purchase	\N	\N
454	0454	31	1	2026-10-08	purchase	\N	\N
455	0455	31	1	2026-10-08	purchase	\N	\N
456	0456	31	1	2026-10-08	purchase	\N	\N
457	0457	31	1	2026-10-08	purchase	\N	\N
458	0458	31	1	2026-10-08	purchase	\N	\N
459	0459	32	1	2026-10-08	purchase	\N	\N
460	0460	32	1	2026-10-08	purchase	\N	\N
461	0461	32	1	2026-10-08	purchase	\N	\N
462	0462	32	1	2026-10-08	purchase	\N	\N
463	0463	32	1	2026-10-08	donation	\N	\N
464	0464	32	1	2026-10-08	purchase	\N	\N
465	0465	32	1	2026-10-08	purchase	\N	\N
466	0466	32	1	2026-10-08	purchase	\N	\N
467	0467	32	1	2026-10-08	purchase	\N	\N
468	0468	33	1	2026-10-08	purchase	\N	\N
469	0469	33	1	2026-10-08	purchase	\N	\N
470	0470	33	1	2026-10-08	purchase	\N	\N
471	0471	33	1	2026-10-08	donation	\N	\N
472	0472	33	1	2026-10-08	purchase	\N	\N
473	0473	33	1	2026-10-08	purchase	\N	\N
474	0474	33	1	2026-10-08	purchase	\N	\N
475	0475	33	1	2026-10-08	purchase	\N	\N
476	0476	33	1	2026-10-08	purchase	\N	\N
477	0477	33	1	2026-10-08	purchase	\N	\N
478	0478	34	1	2026-10-08	purchase	\N	\N
479	0479	34	1	2026-10-08	purchase	\N	\N
480	0480	34	1	2026-10-08	donation	\N	\N
481	0481	34	1	2026-10-08	purchase	\N	\N
482	0482	34	1	2026-10-08	purchase	\N	\N
483	0483	34	1	2026-10-08	purchase	\N	\N
484	0484	34	1	2026-10-08	purchase	\N	\N
485	0485	34	1	2026-10-08	purchase	\N	\N
486	0486	34	1	2026-10-08	purchase	\N	\N
487	0487	34	1	2026-10-08	donation	\N	\N
488	0488	34	1	2026-10-08	purchase	\N	\N
489	0489	34	1	2026-10-08	purchase	\N	\N
490	0490	34	1	2026-10-08	purchase	\N	\N
491	0491	34	1	2026-10-08	purchase	\N	\N
492	0492	35	1	2026-10-08	purchase	\N	\N
493	0493	35	1	2026-10-08	donation	\N	\N
494	0494	35	1	2026-10-08	purchase	\N	\N
495	0495	35	1	2026-10-08	purchase	\N	\N
496	0496	35	1	2026-10-08	purchase	\N	\N
497	0497	35	1	2026-10-08	purchase	\N	\N
498	0498	35	1	2026-10-08	purchase	\N	\N
499	0499	35	1	2026-10-08	purchase	\N	\N
500	0500	35	1	2026-10-08	donation	\N	\N
501	0501	35	1	2026-10-08	purchase	\N	\N
502	0502	36	1	2026-10-08	donation	\N	\N
503	0503	36	1	2026-10-08	purchase	\N	\N
504	0504	36	1	2026-10-08	purchase	\N	\N
505	0505	36	1	2026-10-08	purchase	\N	\N
506	0506	36	1	2026-10-08	purchase	\N	\N
507	0507	36	1	2026-10-08	purchase	\N	\N
508	0508	36	1	2026-10-08	purchase	\N	\N
509	0509	36	1	2026-10-08	donation	\N	\N
510	0510	36	1	2026-10-08	purchase	\N	\N
511	0511	36	1	2026-10-08	purchase	\N	\N
512	0512	37	1	2026-10-08	purchase	\N	\N
513	0513	37	1	2026-10-08	purchase	\N	\N
514	0514	37	1	2026-10-08	purchase	\N	\N
515	0515	37	1	2026-10-08	purchase	\N	\N
516	0516	37	1	2026-10-08	purchase	\N	\N
517	0517	37	1	2026-10-08	purchase	\N	\N
518	0518	37	1	2026-10-08	donation	\N	\N
519	0519	37	1	2026-10-08	purchase	\N	\N
520	0520	38	1	2026-10-08	purchase	\N	\N
521	0521	38	1	2026-10-08	purchase	\N	\N
522	0522	38	1	2026-10-08	purchase	\N	\N
523	0523	38	1	2026-10-08	purchase	\N	\N
524	0524	38	1	2026-10-08	purchase	\N	\N
525	0525	38	1	2026-10-08	donation	\N	\N
526	0526	38	1	2026-10-08	purchase	\N	\N
527	0527	38	1	2026-10-08	purchase	\N	\N
528	0528	38	1	2026-10-08	purchase	\N	\N
529	0529	38	1	2026-10-08	purchase	\N	\N
530	0530	38	1	2026-10-08	purchase	\N	\N
531	0531	38	1	2026-10-08	purchase	\N	\N
532	0532	39	1	2026-10-08	purchase	\N	\N
533	0533	39	1	2026-10-08	purchase	\N	\N
534	0534	39	1	2026-10-08	purchase	\N	\N
535	0535	39	1	2026-10-08	purchase	\N	\N
536	0536	39	1	2026-10-08	donation	\N	\N
537	0537	39	1	2026-10-08	purchase	\N	\N
538	0538	39	1	2026-10-08	purchase	\N	\N
539	0539	39	1	2026-10-08	purchase	\N	\N
540	0540	39	1	2026-10-08	purchase	\N	\N
541	0541	39	1	2026-10-08	purchase	\N	\N
542	0542	39	1	2026-10-08	purchase	\N	\N
543	0543	39	1	2026-10-08	donation	\N	\N
544	0544	40	1	2026-10-08	purchase	\N	\N
545	0545	40	1	2026-10-08	purchase	\N	\N
546	0546	40	1	2026-10-08	purchase	\N	\N
547	0547	40	1	2026-10-08	donation	\N	\N
548	0548	40	1	2026-10-08	purchase	\N	\N
549	0549	40	1	2026-10-08	purchase	\N	\N
550	0550	40	1	2026-10-08	purchase	\N	\N
551	0551	40	1	2026-10-08	purchase	\N	\N
552	0552	40	1	2026-10-08	purchase	\N	\N
553	0553	40	1	2026-10-08	purchase	\N	\N
554	0554	41	1	2026-10-08	purchase	\N	\N
555	0555	41	1	2026-10-08	purchase	\N	\N
556	0556	41	1	2026-10-08	donation	\N	\N
557	0557	41	1	2026-10-08	purchase	\N	\N
558	0558	41	1	2026-10-08	purchase	\N	\N
559	0559	41	1	2026-10-08	purchase	\N	\N
560	0560	41	1	2026-10-08	purchase	\N	\N
561	0561	41	1	2026-10-08	purchase	\N	\N
562	0562	41	1	2026-10-08	purchase	\N	\N
563	0563	42	1	2026-10-08	purchase	\N	\N
564	0564	42	1	2026-10-08	donation	\N	\N
565	0565	42	1	2026-10-08	purchase	\N	\N
566	0566	42	1	2026-10-08	purchase	\N	\N
567	0567	42	1	2026-10-08	purchase	\N	\N
568	0568	42	1	2026-10-08	purchase	\N	\N
569	0569	42	1	2026-10-08	purchase	\N	\N
570	0570	42	1	2026-10-08	purchase	\N	\N
571	0571	43	1	2026-10-08	donation	\N	\N
572	0572	43	1	2026-10-08	purchase	\N	\N
573	0573	43	1	2026-10-08	purchase	\N	\N
574	0574	43	1	2026-10-08	purchase	\N	\N
575	0575	43	1	2026-10-08	purchase	\N	\N
576	0576	43	1	2026-10-08	purchase	\N	\N
577	0577	43	1	2026-10-08	purchase	\N	\N
578	0578	43	1	2026-10-08	donation	\N	\N
579	0579	44	1	2026-10-08	purchase	\N	\N
580	0580	44	1	2026-10-08	purchase	\N	\N
581	0581	44	1	2026-10-08	purchase	\N	\N
582	0582	44	1	2026-10-08	purchase	\N	\N
583	0583	44	1	2026-10-08	purchase	\N	\N
584	0584	44	1	2026-10-08	purchase	\N	\N
585	0585	44	1	2026-10-08	donation	\N	\N
586	0586	44	1	2026-10-08	purchase	\N	\N
587	0587	44	1	2026-10-08	purchase	\N	\N
588	0588	45	1	2026-10-08	purchase	\N	\N
589	0589	45	1	2026-10-08	purchase	\N	\N
590	0590	45	1	2026-10-08	purchase	\N	\N
591	0591	45	1	2026-10-08	purchase	\N	\N
592	0592	45	1	2026-10-08	purchase	\N	\N
593	0593	45	1	2026-10-08	donation	\N	\N
594	0594	45	1	2026-10-08	purchase	\N	\N
595	0595	45	1	2026-10-08	purchase	\N	\N
596	0596	46	1	2026-10-08	purchase	\N	\N
597	0597	46	1	2026-10-08	purchase	\N	\N
598	0598	46	1	2026-10-08	purchase	\N	\N
599	0599	46	1	2026-10-08	purchase	\N	\N
600	0600	46	1	2026-10-08	donation	\N	\N
601	0601	46	1	2026-10-08	purchase	\N	\N
602	0602	46	1	2026-10-08	purchase	\N	\N
603	0603	47	1	2026-10-08	purchase	\N	\N
604	0604	47	1	2026-10-08	purchase	\N	\N
605	0605	47	1	2026-10-08	purchase	\N	\N
606	0606	47	1	2026-10-08	donation	\N	\N
607	0607	47	1	2026-10-08	purchase	\N	\N
608	0608	47	1	2026-10-08	purchase	\N	\N
609	0609	47	1	2026-10-08	purchase	\N	\N
610	0610	47	1	2026-10-08	purchase	\N	\N
611	0611	47	1	2026-10-08	purchase	\N	\N
612	0612	48	1	2026-10-08	purchase	\N	\N
613	0613	48	1	2026-10-08	purchase	\N	\N
614	0614	48	1	2026-10-08	donation	\N	\N
615	0615	48	1	2026-10-08	purchase	\N	\N
616	0616	48	1	2026-10-08	purchase	\N	\N
617	0617	48	1	2026-10-08	purchase	\N	\N
618	0618	48	1	2026-10-08	purchase	\N	\N
619	0619	48	1	2026-10-08	purchase	\N	\N
620	0620	48	1	2026-10-08	purchase	\N	\N
621	0621	48	1	2026-10-08	donation	\N	\N
622	0622	49	1	2026-10-08	purchase	\N	\N
623	0623	49	1	2026-10-08	donation	\N	\N
624	0624	49	1	2026-10-08	purchase	\N	\N
625	0625	49	1	2026-10-08	purchase	\N	\N
626	0626	49	1	2026-10-08	purchase	\N	\N
627	0627	49	1	2026-10-08	purchase	\N	\N
628	0628	49	1	2026-10-08	purchase	\N	\N
629	0629	50	1	2026-10-08	donation	\N	\N
630	0630	51	1	2026-10-08	purchase	\N	\N
631	0631	51	1	2026-10-08	purchase	\N	\N
632	0632	51	1	2026-10-08	purchase	\N	\N
633	0633	51	1	2026-10-08	purchase	\N	\N
634	0634	51	1	2026-10-08	purchase	\N	\N
635	0635	51	1	2026-10-08	purchase	\N	\N
636	0636	51	1	2026-10-08	donation	\N	\N
637	0637	51	1	2026-10-08	purchase	\N	\N
638	0638	51	1	2026-10-08	purchase	\N	\N
639	0639	51	1	2026-10-08	purchase	\N	\N
640	0640	51	1	2026-10-08	purchase	\N	\N
641	0641	51	1	2026-10-08	purchase	\N	\N
642	0642	51	1	2026-10-08	purchase	\N	\N
643	0643	51	1	2026-10-08	donation	\N	\N
644	0644	51	1	2026-10-08	purchase	\N	\N
645	0645	51	1	2026-10-08	purchase	\N	\N
646	0646	51	1	2026-10-08	purchase	\N	\N
647	0647	51	1	2026-10-08	purchase	\N	\N
648	0648	51	1	2026-10-08	purchase	\N	\N
649	0649	51	1	2026-10-08	purchase	\N	\N
650	0650	51	1	2026-10-08	donation	\N	\N
651	0651	51	1	2026-10-08	purchase	\N	\N
652	0652	51	1	2026-10-08	purchase	\N	\N
653	0653	51	1	2026-10-08	purchase	\N	\N
654	0654	52	1	2026-10-08	purchase	\N	\N
655	0655	52	1	2026-10-08	purchase	\N	\N
656	0656	52	1	2026-10-08	purchase	\N	\N
657	0657	52	1	2026-10-08	purchase	\N	\N
658	0658	52	1	2026-10-08	purchase	\N	\N
659	0659	52	1	2026-10-08	donation	\N	\N
660	0660	52	1	2026-10-08	purchase	\N	\N
661	0661	52	1	2026-10-08	purchase	\N	\N
662	0662	52	1	2026-10-08	purchase	\N	\N
663	0663	52	1	2026-10-08	purchase	\N	\N
664	0664	52	1	2026-10-08	purchase	\N	\N
665	0665	52	1	2026-10-08	purchase	\N	\N
666	0666	52	1	2026-10-08	donation	\N	\N
667	0667	52	1	2026-10-08	purchase	\N	\N
668	0668	52	1	2026-10-08	purchase	\N	\N
669	0669	52	1	2026-10-08	purchase	\N	\N
670	0670	52	1	2026-10-08	purchase	\N	\N
671	0671	52	1	2026-10-08	purchase	\N	\N
672	0672	52	1	2026-10-08	purchase	\N	\N
673	0673	52	1	2026-10-08	donation	\N	\N
674	0674	52	1	2026-10-08	purchase	\N	\N
675	0675	52	1	2026-10-08	purchase	\N	\N
676	0676	53	1	2026-10-08	purchase	\N	\N
677	0677	53	1	2026-10-08	purchase	\N	\N
678	0678	53	1	2026-10-08	purchase	\N	\N
679	0679	53	1	2026-10-08	purchase	\N	\N
680	0680	53	1	2026-10-08	donation	\N	\N
681	0681	53	1	2026-10-08	purchase	\N	\N
682	0682	53	1	2026-10-08	purchase	\N	\N
683	0683	53	1	2026-10-08	purchase	\N	\N
684	0684	53	1	2026-10-08	purchase	\N	\N
685	0685	53	1	2026-10-08	purchase	\N	\N
686	0686	53	1	2026-10-08	purchase	\N	\N
687	0687	53	1	2026-10-08	donation	\N	\N
688	0688	53	1	2026-10-08	purchase	\N	\N
689	0689	53	1	2026-10-08	purchase	\N	\N
690	0690	53	1	2026-10-08	purchase	\N	\N
691	0691	53	1	2026-10-08	purchase	\N	\N
692	0692	53	1	2026-10-08	purchase	\N	\N
693	0693	53	1	2026-10-08	purchase	\N	\N
694	0694	53	1	2026-10-08	donation	\N	\N
695	0695	54	1	2026-10-08	purchase	\N	\N
696	0696	54	1	2026-10-08	purchase	\N	\N
697	0697	54	1	2026-10-08	purchase	\N	\N
698	0698	54	1	2026-10-08	donation	\N	\N
699	0699	54	1	2026-10-08	purchase	\N	\N
700	0700	54	1	2026-10-08	purchase	\N	\N
701	0701	54	1	2026-10-08	purchase	\N	\N
702	0702	54	1	2026-10-08	purchase	\N	\N
703	0703	54	1	2026-10-08	purchase	\N	\N
704	0704	54	1	2026-10-08	purchase	\N	\N
705	0705	54	1	2026-10-08	donation	\N	\N
706	0706	54	1	2026-10-08	purchase	\N	\N
707	0707	54	1	2026-10-08	purchase	\N	\N
708	0708	54	1	2026-10-08	purchase	\N	\N
709	0709	54	1	2026-10-08	purchase	\N	\N
710	0710	54	1	2026-10-08	purchase	\N	\N
711	0711	54	1	2026-10-08	purchase	\N	\N
712	0712	54	1	2026-10-08	donation	\N	\N
713	0713	54	1	2026-10-08	purchase	\N	\N
714	0714	55	1	2026-10-08	purchase	\N	\N
715	0715	55	1	2026-10-08	purchase	\N	\N
716	0716	55	1	2026-10-08	donation	\N	\N
717	0717	55	1	2026-10-08	purchase	\N	\N
718	0718	55	1	2026-10-08	purchase	\N	\N
719	0719	55	1	2026-10-08	purchase	\N	\N
720	0720	55	1	2026-10-08	purchase	\N	\N
721	0721	55	1	2026-10-08	purchase	\N	\N
722	0722	55	1	2026-10-08	purchase	\N	\N
723	0723	55	1	2026-10-08	donation	\N	\N
724	0724	55	1	2026-10-08	purchase	\N	\N
725	0725	55	1	2026-10-08	purchase	\N	\N
726	0726	55	1	2026-10-08	purchase	\N	\N
727	0727	55	1	2026-10-08	purchase	\N	\N
728	0728	55	1	2026-10-08	purchase	\N	\N
729	0729	55	1	2026-10-08	purchase	\N	\N
730	0730	55	1	2026-10-08	donation	\N	\N
731	0731	55	1	2026-10-08	purchase	\N	\N
732	0732	55	1	2026-10-08	purchase	\N	\N
733	0733	55	1	2026-10-08	purchase	\N	\N
734	0734	55	1	2026-10-08	purchase	\N	\N
735	0735	55	1	2026-10-08	purchase	\N	\N
736	0736	55	1	2026-10-08	purchase	\N	\N
737	0737	55	1	2026-10-08	donation	\N	\N
738	0738	56	1	2026-10-08	purchase	\N	\N
739	0739	56	1	2026-10-08	donation	\N	\N
740	0740	56	1	2026-10-08	purchase	\N	\N
741	0741	56	1	2026-10-08	purchase	\N	\N
742	0742	56	1	2026-10-08	purchase	\N	\N
743	0743	56	1	2026-10-08	purchase	\N	\N
744	0744	56	1	2026-10-08	purchase	\N	\N
745	0745	56	1	2026-10-08	purchase	\N	\N
746	0746	56	1	2026-10-08	donation	\N	\N
747	0747	56	1	2026-10-08	purchase	\N	\N
748	0748	56	1	2026-10-08	purchase	\N	\N
749	0749	56	1	2026-10-08	purchase	\N	\N
750	0750	56	1	2026-10-08	purchase	\N	\N
751	0751	56	1	2026-10-08	purchase	\N	\N
752	0752	56	1	2026-10-08	purchase	\N	\N
753	0753	56	1	2026-10-08	donation	\N	\N
754	0754	56	1	2026-10-08	purchase	\N	\N
755	0755	56	1	2026-10-08	purchase	\N	\N
756	0756	56	1	2026-10-08	purchase	\N	\N
757	0757	56	1	2026-10-08	purchase	\N	\N
758	0758	57	1	2026-10-08	donation	\N	\N
759	0759	57	1	2026-10-08	purchase	\N	\N
760	0760	57	1	2026-10-08	purchase	\N	\N
761	0761	57	1	2026-10-08	purchase	\N	\N
762	0762	57	1	2026-10-08	purchase	\N	\N
763	0763	57	1	2026-10-08	purchase	\N	\N
764	0764	57	1	2026-10-08	purchase	\N	\N
765	0765	57	1	2026-10-08	donation	\N	\N
766	0766	57	1	2026-10-08	purchase	\N	\N
767	0767	57	1	2026-10-08	purchase	\N	\N
768	0768	57	1	2026-10-08	purchase	\N	\N
769	0769	57	1	2026-10-08	purchase	\N	\N
770	0770	57	1	2026-10-08	purchase	\N	\N
771	0771	57	1	2026-10-08	purchase	\N	\N
772	0772	57	1	2026-10-08	donation	\N	\N
773	0773	57	1	2026-10-08	purchase	\N	\N
774	0774	57	1	2026-10-08	purchase	\N	\N
775	0775	57	1	2026-10-08	purchase	\N	\N
776	0776	57	1	2026-10-08	purchase	\N	\N
777	0777	57	1	2026-10-08	purchase	\N	\N
778	0778	58	1	2026-10-08	purchase	\N	\N
779	0779	58	1	2026-10-08	purchase	\N	\N
780	0780	58	1	2026-10-08	purchase	\N	\N
781	0781	58	1	2026-10-08	purchase	\N	\N
782	0782	58	1	2026-10-08	purchase	\N	\N
783	0783	58	1	2026-10-08	purchase	\N	\N
784	0784	58	1	2026-10-08	donation	\N	\N
785	0785	58	1	2026-10-08	purchase	\N	\N
786	0786	58	1	2026-10-08	purchase	\N	\N
787	0787	58	1	2026-10-08	purchase	\N	\N
788	0788	58	1	2026-10-08	purchase	\N	\N
789	0789	58	1	2026-10-08	purchase	\N	\N
790	0790	58	1	2026-10-08	purchase	\N	\N
791	0791	58	1	2026-10-08	donation	\N	\N
792	0792	58	1	2026-10-08	purchase	\N	\N
793	0793	58	1	2026-10-08	purchase	\N	\N
794	0794	58	1	2026-10-08	purchase	\N	\N
795	0795	58	1	2026-10-08	purchase	\N	\N
796	0796	58	1	2026-10-08	purchase	\N	\N
797	0797	58	1	2026-10-08	purchase	\N	\N
798	0798	59	1	2026-10-08	purchase	\N	\N
799	0799	59	1	2026-10-08	purchase	\N	\N
800	0800	59	1	2026-10-08	purchase	\N	\N
801	0801	59	1	2026-10-08	purchase	\N	\N
802	0802	59	1	2026-10-08	purchase	\N	\N
803	0803	59	1	2026-10-08	donation	\N	\N
804	0804	59	1	2026-10-08	purchase	\N	\N
805	0805	59	1	2026-10-08	purchase	\N	\N
806	0806	59	1	2026-10-08	purchase	\N	\N
807	0807	59	1	2026-10-08	purchase	\N	\N
808	0808	59	1	2026-10-08	purchase	\N	\N
809	0809	59	1	2026-10-08	purchase	\N	\N
810	0810	59	1	2026-10-08	donation	\N	\N
811	0811	59	1	2026-10-08	purchase	\N	\N
812	0812	59	1	2026-10-08	purchase	\N	\N
813	0813	59	1	2026-10-08	purchase	\N	\N
814	0814	59	1	2026-10-08	purchase	\N	\N
815	0815	59	1	2026-10-08	purchase	\N	\N
816	0816	60	1	2026-10-08	purchase	\N	\N
817	0817	60	1	2026-10-08	purchase	\N	\N
818	0818	60	1	2026-10-08	purchase	\N	\N
819	0819	60	1	2026-10-08	purchase	\N	\N
820	0820	60	1	2026-10-08	donation	\N	\N
821	0821	60	1	2026-10-08	purchase	\N	\N
822	0822	60	1	2026-10-08	purchase	\N	\N
823	0823	60	1	2026-10-08	purchase	\N	\N
824	0824	60	1	2026-10-08	purchase	\N	\N
825	0825	60	1	2026-10-08	purchase	\N	\N
826	0826	60	1	2026-10-08	purchase	\N	\N
827	0827	60	1	2026-10-08	donation	\N	\N
828	0828	60	1	2026-10-08	purchase	\N	\N
829	0829	60	1	2026-10-08	purchase	\N	\N
830	0830	60	1	2026-10-08	purchase	\N	\N
831	0831	60	1	2026-10-08	purchase	\N	\N
832	0832	60	1	2026-10-08	purchase	\N	\N
833	0833	60	1	2026-10-08	purchase	\N	\N
834	0834	60	1	2026-10-08	donation	\N	\N
835	0835	60	1	2026-10-08	purchase	\N	\N
836	0836	61	1	2026-10-08	purchase	\N	\N
837	0837	61	1	2026-10-08	purchase	\N	\N
838	0838	61	1	2026-10-08	purchase	\N	\N
839	0839	61	1	2026-10-08	donation	\N	\N
840	0840	61	1	2026-10-08	purchase	\N	\N
841	0841	61	1	2026-10-08	purchase	\N	\N
842	0842	61	1	2026-10-08	purchase	\N	\N
843	0843	61	1	2026-10-08	purchase	\N	\N
844	0844	61	1	2026-10-08	purchase	\N	\N
845	0845	61	1	2026-10-08	purchase	\N	\N
846	0846	61	1	2026-10-08	donation	\N	\N
847	0847	61	1	2026-10-08	purchase	\N	\N
848	0848	61	1	2026-10-08	purchase	\N	\N
849	0849	61	1	2026-10-08	purchase	\N	\N
850	0850	61	1	2026-10-08	purchase	\N	\N
851	0851	61	1	2026-10-08	purchase	\N	\N
852	0852	61	1	2026-10-08	purchase	\N	\N
853	0853	61	1	2026-10-08	donation	\N	\N
854	0854	61	1	2026-10-08	purchase	\N	\N
855	0855	61	1	2026-10-08	purchase	\N	\N
856	0856	61	1	2026-10-08	purchase	\N	\N
857	0857	61	1	2026-10-08	purchase	\N	\N
858	0858	62	1	2026-10-08	purchase	\N	\N
859	0859	62	1	2026-10-08	purchase	\N	\N
860	0860	62	1	2026-10-08	donation	\N	\N
861	0861	62	1	2026-10-08	purchase	\N	\N
862	0862	62	1	2026-10-08	purchase	\N	\N
863	0863	62	1	2026-10-08	purchase	\N	\N
864	0864	62	1	2026-10-08	purchase	\N	\N
865	0865	62	1	2026-10-08	purchase	\N	\N
866	0866	62	1	2026-10-08	purchase	\N	\N
867	0867	62	1	2026-10-08	donation	\N	\N
868	0868	62	1	2026-10-08	purchase	\N	\N
869	0869	62	1	2026-10-08	purchase	\N	\N
870	0870	62	1	2026-10-08	purchase	\N	\N
871	0871	62	1	2026-10-08	purchase	\N	\N
872	0872	62	1	2026-10-08	purchase	\N	\N
873	0873	62	1	2026-10-08	purchase	\N	\N
874	0874	62	1	2026-10-08	donation	\N	\N
875	0875	62	1	2026-10-08	purchase	\N	\N
876	0876	63	1	2026-10-08	purchase	\N	\N
877	0877	63	1	2026-10-08	donation	\N	\N
878	0878	63	1	2026-10-08	purchase	\N	\N
879	0879	63	1	2026-10-08	purchase	\N	\N
880	0880	63	1	2026-10-08	purchase	\N	\N
881	0881	63	1	2026-10-08	purchase	\N	\N
882	0882	63	1	2026-10-08	purchase	\N	\N
883	0883	63	1	2026-10-08	purchase	\N	\N
884	0884	63	1	2026-10-08	donation	\N	\N
885	0885	63	1	2026-10-08	purchase	\N	\N
886	0886	63	1	2026-10-08	purchase	\N	\N
887	0887	63	1	2026-10-08	purchase	\N	\N
888	0888	63	1	2026-10-08	purchase	\N	\N
889	0889	63	1	2026-10-08	purchase	\N	\N
890	0890	63	1	2026-10-08	purchase	\N	\N
891	0891	63	1	2026-10-08	donation	\N	\N
892	0892	63	1	2026-10-08	purchase	\N	\N
893	0893	63	1	2026-10-08	purchase	\N	\N
894	0894	63	1	2026-10-08	purchase	\N	\N
895	0895	63	1	2026-10-08	purchase	\N	\N
896	0896	64	1	2026-10-08	donation	\N	\N
897	0897	64	1	2026-10-08	purchase	\N	\N
898	0898	64	1	2026-10-08	purchase	\N	\N
899	0899	64	1	2026-10-08	purchase	\N	\N
900	0900	64	1	2026-10-08	purchase	\N	\N
901	0901	64	1	2026-10-08	purchase	\N	\N
902	0902	64	1	2026-10-08	purchase	\N	\N
903	0903	64	1	2026-10-08	donation	\N	\N
904	0904	64	1	2026-10-08	purchase	\N	\N
905	0905	64	1	2026-10-08	purchase	\N	\N
906	0906	64	1	2026-10-08	purchase	\N	\N
907	0907	64	1	2026-10-08	purchase	\N	\N
908	0908	64	1	2026-10-08	purchase	\N	\N
909	0909	64	1	2026-10-08	purchase	\N	\N
910	0910	64	1	2026-10-08	donation	\N	\N
911	0911	64	1	2026-10-08	purchase	\N	\N
912	0912	64	1	2026-10-08	purchase	\N	\N
913	0913	64	1	2026-10-08	purchase	\N	\N
914	0914	65	1	2026-10-08	purchase	\N	\N
915	0915	65	1	2026-10-08	purchase	\N	\N
916	0916	65	1	2026-10-08	purchase	\N	\N
917	0917	65	1	2026-10-08	purchase	\N	\N
918	0918	65	1	2026-10-08	purchase	\N	\N
919	0919	65	1	2026-10-08	purchase	\N	\N
920	0920	65	1	2026-10-08	donation	\N	\N
921	0921	65	1	2026-10-08	purchase	\N	\N
922	0922	65	1	2026-10-08	purchase	\N	\N
923	0923	65	1	2026-10-08	purchase	\N	\N
924	0924	65	1	2026-10-08	purchase	\N	\N
925	0925	65	1	2026-10-08	purchase	\N	\N
926	0926	65	1	2026-10-08	purchase	\N	\N
927	0927	65	1	2026-10-08	donation	\N	\N
928	0928	66	1	2026-10-08	purchase	\N	\N
929	0929	66	1	2026-10-08	purchase	\N	\N
930	0930	66	1	2026-10-08	purchase	\N	\N
931	0931	66	1	2026-10-08	purchase	\N	\N
932	0932	66	1	2026-10-08	purchase	\N	\N
933	0933	66	1	2026-10-08	donation	\N	\N
934	0934	66	1	2026-10-08	purchase	\N	\N
935	0935	66	1	2026-10-08	purchase	\N	\N
936	0936	66	1	2026-10-08	purchase	\N	\N
937	0937	66	1	2026-10-08	purchase	\N	\N
938	0938	66	1	2026-10-08	purchase	\N	\N
939	0939	66	1	2026-10-08	purchase	\N	\N
940	0940	66	1	2026-10-08	donation	\N	\N
941	0941	66	1	2026-10-08	purchase	\N	\N
942	0942	67	1	2026-10-08	purchase	\N	\N
943	0943	67	1	2026-10-08	purchase	\N	\N
944	0944	67	1	2026-10-08	purchase	\N	\N
945	0945	67	1	2026-10-08	purchase	\N	\N
946	0946	67	1	2026-10-08	donation	\N	\N
947	0947	67	1	2026-10-08	purchase	\N	\N
948	0948	67	1	2026-10-08	purchase	\N	\N
949	0949	67	1	2026-10-08	purchase	\N	\N
950	0950	67	1	2026-10-08	purchase	\N	\N
951	0951	67	1	2026-10-08	purchase	\N	\N
952	0952	67	1	2026-10-08	purchase	\N	\N
953	0953	67	1	2026-10-08	donation	\N	\N
954	0954	67	1	2026-10-08	purchase	\N	\N
955	0955	67	1	2026-10-08	purchase	\N	\N
956	0956	67	1	2026-10-08	purchase	\N	\N
957	0957	67	1	2026-10-08	purchase	\N	\N
958	0958	68	1	2026-10-08	purchase	\N	\N
959	0959	68	1	2026-10-08	purchase	\N	\N
960	0960	68	1	2026-10-08	purchase	\N	\N
961	0961	68	1	2026-10-08	donation	\N	\N
962	0962	68	1	2026-10-08	purchase	\N	\N
963	0963	68	1	2026-10-08	purchase	\N	\N
964	0964	68	1	2026-10-08	purchase	\N	\N
965	0965	68	1	2026-10-08	purchase	\N	\N
966	0966	68	1	2026-10-08	purchase	\N	\N
967	0967	68	1	2026-10-08	purchase	\N	\N
968	0968	68	1	2026-10-08	donation	\N	\N
969	0969	68	1	2026-10-08	purchase	\N	\N
970	0970	68	1	2026-10-08	purchase	\N	\N
971	0971	68	1	2026-10-08	purchase	\N	\N
972	0972	68	1	2026-10-08	purchase	\N	\N
973	0973	68	1	2026-10-08	purchase	\N	\N
974	0974	68	1	2026-10-08	purchase	\N	\N
975	0975	68	1	2026-10-08	donation	\N	\N
976	0976	69	1	2026-10-08	purchase	\N	\N
977	0977	69	1	2026-10-08	purchase	\N	\N
978	0978	69	1	2026-10-08	donation	\N	\N
979	0979	69	1	2026-10-08	purchase	\N	\N
980	0980	69	1	2026-10-08	purchase	\N	\N
981	0981	69	1	2026-10-08	purchase	\N	\N
982	0982	69	1	2026-10-08	purchase	\N	\N
983	0983	69	1	2026-10-08	purchase	\N	\N
984	0984	69	1	2026-10-08	purchase	\N	\N
985	0985	69	1	2026-10-08	donation	\N	\N
986	0986	69	1	2026-10-08	purchase	\N	\N
987	0987	69	1	2026-10-08	purchase	\N	\N
988	0988	69	1	2026-10-08	purchase	\N	\N
989	0989	69	1	2026-10-08	purchase	\N	\N
990	0990	69	1	2026-10-08	purchase	\N	\N
991	0991	69	1	2026-10-08	purchase	\N	\N
992	0992	70	1	2026-10-08	purchase	\N	\N
993	0993	70	1	2026-10-08	donation	\N	\N
994	0994	70	1	2026-10-08	purchase	\N	\N
995	0995	70	1	2026-10-08	purchase	\N	\N
996	0996	70	1	2026-10-08	purchase	\N	\N
997	0997	70	1	2026-10-08	purchase	\N	\N
998	0998	70	1	2026-10-08	purchase	\N	\N
999	0999	70	1	2026-10-08	purchase	\N	\N
1000	1000	70	1	2026-10-08	donation	\N	\N
1001	1001	70	1	2026-10-08	purchase	\N	\N
1002	1002	70	1	2026-10-08	purchase	\N	\N
1003	1003	70	1	2026-10-08	purchase	\N	\N
1004	1004	71	1	2026-10-08	donation	\N	\N
1005	1005	71	1	2026-10-08	purchase	\N	\N
1006	1006	71	1	2026-10-08	purchase	\N	\N
1007	1007	71	1	2026-10-08	purchase	\N	\N
1008	1008	71	1	2026-10-08	purchase	\N	\N
1009	1009	71	1	2026-10-08	purchase	\N	\N
1010	1010	71	1	2026-10-08	purchase	\N	\N
1011	1011	71	1	2026-10-08	donation	\N	\N
1012	1012	71	1	2026-10-08	purchase	\N	\N
1013	1013	71	1	2026-10-08	purchase	\N	\N
1014	1014	71	1	2026-10-08	purchase	\N	\N
1015	1015	71	1	2026-10-08	purchase	\N	\N
1016	1016	71	1	2026-10-08	purchase	\N	\N
1017	1017	71	1	2026-10-08	purchase	\N	\N
1018	1018	72	1	2026-10-08	purchase	\N	\N
1019	1019	72	1	2026-10-08	purchase	\N	\N
1020	1020	72	1	2026-10-08	purchase	\N	\N
1021	1021	72	1	2026-10-08	purchase	\N	\N
1022	1022	72	1	2026-10-08	purchase	\N	\N
1023	1023	72	1	2026-10-08	purchase	\N	\N
1024	1024	72	1	2026-10-08	donation	\N	\N
1025	1025	72	1	2026-10-08	purchase	\N	\N
1026	1026	72	1	2026-10-08	purchase	\N	\N
1027	1027	72	1	2026-10-08	purchase	\N	\N
1028	1028	72	1	2026-10-08	purchase	\N	\N
1029	1029	72	1	2026-10-08	purchase	\N	\N
1030	1030	73	1	2026-10-08	purchase	\N	\N
1031	1031	73	1	2026-10-08	purchase	\N	\N
1032	1032	73	1	2026-10-08	purchase	\N	\N
1033	1033	73	1	2026-10-08	purchase	\N	\N
1034	1034	73	1	2026-10-08	purchase	\N	\N
1035	1035	73	1	2026-10-08	donation	\N	\N
1036	1036	73	1	2026-10-08	purchase	\N	\N
1037	1037	73	1	2026-10-08	purchase	\N	\N
1038	1038	73	1	2026-10-08	purchase	\N	\N
1039	1039	73	1	2026-10-08	purchase	\N	\N
1040	1040	73	1	2026-10-08	purchase	\N	\N
1041	1041	73	1	2026-10-08	purchase	\N	\N
1042	1042	73	1	2026-10-08	donation	\N	\N
1043	1043	73	1	2026-10-08	purchase	\N	\N
1044	1044	74	1	2026-10-08	purchase	\N	\N
1045	1045	74	1	2026-10-08	purchase	\N	\N
1046	1046	74	1	2026-10-08	purchase	\N	\N
1047	1047	74	1	2026-10-08	purchase	\N	\N
1048	1048	74	1	2026-10-08	donation	\N	\N
1049	1049	74	1	2026-10-08	purchase	\N	\N
1050	1050	74	1	2026-10-08	purchase	\N	\N
1051	1051	74	1	2026-10-08	purchase	\N	\N
1052	1052	74	1	2026-10-08	purchase	\N	\N
1053	1053	74	1	2026-10-08	purchase	\N	\N
1054	1054	74	1	2026-10-08	purchase	\N	\N
1055	1055	74	1	2026-10-08	donation	\N	\N
1056	1056	74	1	2026-10-08	purchase	\N	\N
1057	1057	74	1	2026-10-08	purchase	\N	\N
1058	1058	75	1	2026-10-08	purchase	\N	\N
1059	1059	75	1	2026-10-08	purchase	\N	\N
1060	1060	75	1	2026-10-08	purchase	\N	\N
1061	1061	75	1	2026-10-08	donation	\N	\N
1062	1062	75	1	2026-10-08	purchase	\N	\N
1063	1063	75	1	2026-10-08	purchase	\N	\N
1064	1064	75	1	2026-10-08	purchase	\N	\N
1065	1065	75	1	2026-10-08	purchase	\N	\N
1066	1066	75	1	2026-10-08	purchase	\N	\N
1067	1067	75	1	2026-10-08	purchase	\N	\N
1068	1068	75	1	2026-10-08	donation	\N	\N
1069	1069	75	1	2026-10-08	purchase	\N	\N
1070	1070	75	1	2026-10-08	purchase	\N	\N
1071	1071	75	1	2026-10-08	purchase	\N	\N
1072	1072	76	1	2026-10-08	purchase	\N	\N
1073	1073	76	1	2026-10-08	purchase	\N	\N
1074	1074	76	1	2026-10-08	donation	\N	\N
1075	1075	76	1	2026-10-08	purchase	\N	\N
1076	1076	76	1	2026-10-08	purchase	\N	\N
1077	1077	76	1	2026-10-08	purchase	\N	\N
1078	1078	76	1	2026-10-08	purchase	\N	\N
1079	1079	76	1	2026-10-08	purchase	\N	\N
1080	1080	76	1	2026-10-08	purchase	\N	\N
1081	1081	76	1	2026-10-08	donation	\N	\N
1082	1082	76	1	2026-10-08	purchase	\N	\N
1083	1083	76	1	2026-10-08	purchase	\N	\N
1084	1084	76	1	2026-10-08	purchase	\N	\N
1085	1085	76	1	2026-10-08	purchase	\N	\N
1086	1086	77	1	2026-10-08	purchase	\N	\N
1087	1087	77	1	2026-10-08	donation	\N	\N
1088	1088	77	1	2026-10-08	purchase	\N	\N
1089	1089	77	1	2026-10-08	purchase	\N	\N
1090	1090	77	1	2026-10-08	purchase	\N	\N
1091	1091	77	1	2026-10-08	purchase	\N	\N
1092	1092	77	1	2026-10-08	purchase	\N	\N
1093	1093	77	1	2026-10-08	purchase	\N	\N
1094	1094	77	1	2026-10-08	donation	\N	\N
1095	1095	77	1	2026-10-08	purchase	\N	\N
1096	1096	77	1	2026-10-08	purchase	\N	\N
1097	1097	77	1	2026-10-08	purchase	\N	\N
1098	1098	77	1	2026-10-08	purchase	\N	\N
1099	1099	77	1	2026-10-08	purchase	\N	\N
1100	1100	78	1	2026-10-08	donation	\N	\N
1101	1101	78	1	2026-10-08	purchase	\N	\N
1102	1102	78	1	2026-10-08	purchase	\N	\N
1103	1103	78	1	2026-10-08	purchase	\N	\N
1104	1104	78	1	2026-10-08	purchase	\N	\N
1105	1105	78	1	2026-10-08	purchase	\N	\N
1106	1106	78	1	2026-10-08	purchase	\N	\N
1107	1107	78	1	2026-10-08	donation	\N	\N
1108	1108	78	1	2026-10-08	purchase	\N	\N
1109	1109	78	1	2026-10-08	purchase	\N	\N
1110	1110	78	1	2026-10-08	purchase	\N	\N
1111	1111	78	1	2026-10-08	purchase	\N	\N
1112	1112	78	1	2026-10-08	purchase	\N	\N
1113	1113	78	1	2026-10-08	purchase	\N	\N
1114	1114	78	1	2026-10-08	donation	\N	\N
1115	1115	78	1	2026-10-08	purchase	\N	\N
1116	1116	79	1	2026-10-08	purchase	\N	\N
1117	1117	79	1	2026-10-08	purchase	\N	\N
1118	1118	79	1	2026-10-08	purchase	\N	\N
1119	1119	79	1	2026-10-08	purchase	\N	\N
1120	1120	79	1	2026-10-08	purchase	\N	\N
1121	1121	79	1	2026-10-08	purchase	\N	\N
1122	1122	79	1	2026-10-08	donation	\N	\N
1123	1123	79	1	2026-10-08	purchase	\N	\N
1124	1124	79	1	2026-10-08	purchase	\N	\N
1125	1125	79	1	2026-10-08	purchase	\N	\N
1126	1126	79	1	2026-10-08	purchase	\N	\N
1127	1127	79	1	2026-10-08	purchase	\N	\N
1128	1128	80	1	2026-10-08	purchase	\N	\N
1129	1129	80	1	2026-10-08	purchase	\N	\N
1130	1130	80	1	2026-10-08	purchase	\N	\N
1131	1131	80	1	2026-10-08	purchase	\N	\N
1132	1132	80	1	2026-10-08	purchase	\N	\N
1133	1133	80	1	2026-10-08	donation	\N	\N
1134	1134	80	1	2026-10-08	purchase	\N	\N
1135	1135	80	1	2026-10-08	purchase	\N	\N
1136	1136	80	1	2026-10-08	purchase	\N	\N
1137	1137	80	1	2026-10-08	purchase	\N	\N
1138	1138	80	1	2026-10-08	purchase	\N	\N
1139	1139	80	1	2026-10-08	purchase	\N	\N
1140	1140	80	1	2026-10-08	donation	\N	\N
1141	1141	80	1	2026-10-08	purchase	\N	\N
1142	1142	81	1	2026-10-08	purchase	\N	\N
1143	1143	81	1	2026-10-08	purchase	\N	\N
1144	1144	81	1	2026-10-08	purchase	\N	\N
1145	1145	81	1	2026-10-08	purchase	\N	\N
1146	1146	81	1	2026-10-08	donation	\N	\N
1147	1147	81	1	2026-10-08	purchase	\N	\N
1148	1148	81	1	2026-10-08	purchase	\N	\N
1149	1149	81	1	2026-10-08	purchase	\N	\N
1150	1150	81	1	2026-10-08	purchase	\N	\N
1151	1151	81	1	2026-10-08	purchase	\N	\N
1152	1152	81	1	2026-10-08	purchase	\N	\N
1153	1153	81	1	2026-10-08	donation	\N	\N
1154	1154	82	1	2026-10-08	purchase	\N	\N
1155	1155	82	1	2026-10-08	purchase	\N	\N
1156	1156	82	1	2026-10-08	purchase	\N	\N
1157	1157	82	1	2026-10-08	donation	\N	\N
1158	1158	82	1	2026-10-08	purchase	\N	\N
1159	1159	82	1	2026-10-08	purchase	\N	\N
1160	1160	82	1	2026-10-08	purchase	\N	\N
1161	1161	82	1	2026-10-08	purchase	\N	\N
1162	1162	82	1	2026-10-08	purchase	\N	\N
1163	1163	82	1	2026-10-08	purchase	\N	\N
1164	1164	83	1	2026-10-08	purchase	\N	\N
1165	1165	83	1	2026-10-08	purchase	\N	\N
1166	1166	83	1	2026-10-08	donation	\N	\N
1167	1167	83	1	2026-10-08	purchase	\N	\N
1168	1168	83	1	2026-10-08	purchase	\N	\N
1169	1169	83	1	2026-10-08	purchase	\N	\N
1170	1170	83	1	2026-10-08	purchase	\N	\N
1171	1171	83	1	2026-10-08	purchase	\N	\N
1172	1172	83	1	2026-10-08	purchase	\N	\N
1173	1173	84	1	2026-10-08	purchase	\N	\N
1174	1174	84	1	2026-10-08	donation	\N	\N
1175	1175	84	1	2026-10-08	purchase	\N	\N
1176	1176	84	1	2026-10-08	purchase	\N	\N
1177	1177	84	1	2026-10-08	purchase	\N	\N
1178	1178	84	1	2026-10-08	purchase	\N	\N
1179	1179	84	1	2026-10-08	purchase	\N	\N
1180	1180	84	1	2026-10-08	purchase	\N	\N
1181	1181	84	1	2026-10-08	donation	\N	\N
1182	1182	84	1	2026-10-08	purchase	\N	\N
1183	1183	84	1	2026-10-08	purchase	\N	\N
1184	1184	84	1	2026-10-08	purchase	\N	\N
1185	1185	85	1	2026-10-08	donation	\N	\N
1186	1186	85	1	2026-10-08	purchase	\N	\N
1187	1187	85	1	2026-10-08	purchase	\N	\N
1188	1188	85	1	2026-10-08	purchase	\N	\N
1189	1189	85	1	2026-10-08	purchase	\N	\N
1190	1190	85	1	2026-10-08	purchase	\N	\N
1191	1191	85	1	2026-10-08	purchase	\N	\N
1192	1192	85	1	2026-10-08	donation	\N	\N
1193	1193	85	1	2026-10-08	purchase	\N	\N
1194	1194	85	1	2026-10-08	purchase	\N	\N
1195	1195	85	1	2026-10-08	purchase	\N	\N
1196	1196	85	1	2026-10-08	purchase	\N	\N
1197	1197	86	1	2026-10-08	purchase	\N	\N
1198	1198	86	1	2026-10-08	purchase	\N	\N
1199	1199	86	1	2026-10-08	purchase	\N	\N
1200	1200	86	1	2026-10-08	purchase	\N	\N
1201	1201	86	1	2026-10-08	purchase	\N	\N
1202	1202	86	1	2026-10-08	purchase	\N	\N
1203	1203	86	1	2026-10-08	donation	\N	\N
1204	1204	86	1	2026-10-08	purchase	\N	\N
1205	1205	86	1	2026-10-08	purchase	\N	\N
1206	1206	86	1	2026-10-08	purchase	\N	\N
1207	1207	86	1	2026-10-08	purchase	\N	\N
1208	1208	86	1	2026-10-08	purchase	\N	\N
1209	1209	86	1	2026-10-08	purchase	\N	\N
1210	1210	86	1	2026-10-08	donation	\N	\N
1211	1211	87	1	2026-10-08	purchase	\N	\N
1212	1212	87	1	2026-10-08	purchase	\N	\N
1213	1213	87	1	2026-10-08	purchase	\N	\N
1214	1214	87	1	2026-10-08	purchase	\N	\N
1215	1215	87	1	2026-10-08	purchase	\N	\N
1216	1216	87	1	2026-10-08	donation	\N	\N
1217	1217	87	1	2026-10-08	purchase	\N	\N
1218	1218	87	1	2026-10-08	purchase	\N	\N
1219	1219	87	1	2026-10-08	purchase	\N	\N
1220	1220	87	1	2026-10-08	purchase	\N	\N
1221	1221	88	1	2026-10-08	purchase	\N	\N
1222	1222	88	1	2026-10-08	purchase	\N	\N
1223	1223	88	1	2026-10-08	purchase	\N	\N
1224	1224	88	1	2026-10-08	purchase	\N	\N
1225	1225	88	1	2026-10-08	donation	\N	\N
1226	1226	88	1	2026-10-08	purchase	\N	\N
1227	1227	88	1	2026-10-08	purchase	\N	\N
1228	1228	88	1	2026-10-08	purchase	\N	\N
1229	1229	88	1	2026-10-08	purchase	\N	\N
1230	1230	89	1	2026-10-08	purchase	\N	\N
1231	1231	89	1	2026-10-08	purchase	\N	\N
1232	1232	89	1	2026-10-08	purchase	\N	\N
1233	1233	89	1	2026-10-08	donation	\N	\N
1234	1234	89	1	2026-10-08	purchase	\N	\N
1235	1235	89	1	2026-10-08	purchase	\N	\N
1236	1236	89	1	2026-10-08	purchase	\N	\N
1237	1237	89	1	2026-10-08	purchase	\N	\N
1238	1238	89	1	2026-10-08	purchase	\N	\N
1239	1239	89	1	2026-10-08	purchase	\N	\N
1240	1240	89	1	2026-10-08	donation	\N	\N
1241	1241	89	1	2026-10-08	purchase	\N	\N
1242	1242	89	1	2026-10-08	purchase	\N	\N
1243	1243	89	1	2026-10-08	purchase	\N	\N
1244	1244	90	1	2026-10-08	purchase	\N	\N
1245	1245	90	1	2026-10-08	purchase	\N	\N
1246	1246	90	1	2026-10-08	donation	\N	\N
1247	1247	90	1	2026-10-08	purchase	\N	\N
1248	1248	90	1	2026-10-08	purchase	\N	\N
1249	1249	90	1	2026-10-08	purchase	\N	\N
1250	1250	90	1	2026-10-08	purchase	\N	\N
1251	1251	90	1	2026-10-08	purchase	\N	\N
1252	1252	90	1	2026-10-08	purchase	\N	\N
1253	1253	90	1	2026-10-08	donation	\N	\N
1254	1254	91	1	2026-10-08	purchase	\N	\N
1255	1255	91	1	2026-10-08	donation	\N	\N
1256	1256	91	1	2026-10-08	purchase	\N	\N
1257	1257	91	1	2026-10-08	purchase	\N	\N
1258	1258	91	1	2026-10-08	purchase	\N	\N
1259	1259	91	1	2026-10-08	purchase	\N	\N
1260	1260	91	1	2026-10-08	purchase	\N	\N
1261	1261	91	1	2026-10-08	purchase	\N	\N
1262	1262	91	1	2026-10-08	donation	\N	\N
1263	1263	91	1	2026-10-08	purchase	\N	\N
1264	1264	92	1	2026-10-08	donation	\N	\N
1265	1265	92	1	2026-10-08	purchase	\N	\N
1266	1266	92	1	2026-10-08	purchase	\N	\N
1267	1267	92	1	2026-10-08	purchase	\N	\N
1268	1268	92	1	2026-10-08	purchase	\N	\N
1269	1269	92	1	2026-10-08	purchase	\N	\N
1270	1270	92	1	2026-10-08	purchase	\N	\N
1271	1271	92	1	2026-10-08	donation	\N	\N
1272	1272	92	1	2026-10-08	purchase	\N	\N
1273	1273	92	1	2026-10-08	purchase	\N	\N
1274	1274	93	1	2026-10-08	purchase	\N	\N
1275	1275	93	1	2026-10-08	purchase	\N	\N
1276	1276	93	1	2026-10-08	purchase	\N	\N
1277	1277	93	1	2026-10-08	purchase	\N	\N
1278	1278	93	1	2026-10-08	purchase	\N	\N
1279	1279	93	1	2026-10-08	purchase	\N	\N
1280	1280	93	1	2026-10-08	donation	\N	\N
1281	1281	93	1	2026-10-08	purchase	\N	\N
1282	1282	93	1	2026-10-08	purchase	\N	\N
1283	1283	93	1	2026-10-08	purchase	\N	\N
1284	1284	93	1	2026-10-08	purchase	\N	\N
1285	1285	93	1	2026-10-08	purchase	\N	\N
1286	1286	94	1	2026-10-08	purchase	\N	\N
1287	1287	94	1	2026-10-08	purchase	\N	\N
1288	1288	94	1	2026-10-08	purchase	\N	\N
1289	1289	94	1	2026-10-08	purchase	\N	\N
1290	1290	94	1	2026-10-08	purchase	\N	\N
1291	1291	94	1	2026-10-08	donation	\N	\N
1292	1292	94	1	2026-10-08	purchase	\N	\N
1293	1293	94	1	2026-10-08	purchase	\N	\N
1294	1294	94	1	2026-10-08	purchase	\N	\N
1295	1295	95	1	2026-10-08	purchase	\N	\N
1296	1296	95	1	2026-10-08	purchase	\N	\N
1297	1297	95	1	2026-10-08	purchase	\N	\N
1298	1298	95	1	2026-10-08	purchase	\N	\N
1299	1299	95	1	2026-10-08	donation	\N	\N
1300	1300	95	1	2026-10-08	purchase	\N	\N
1301	1301	95	1	2026-10-08	purchase	\N	\N
1302	1302	95	1	2026-10-08	purchase	\N	\N
1303	1303	95	1	2026-10-08	purchase	\N	\N
1304	1304	95	1	2026-10-08	purchase	\N	\N
1305	1305	95	1	2026-10-08	purchase	\N	\N
1306	1306	95	1	2026-10-08	donation	\N	\N
1307	1307	96	1	2026-10-08	purchase	\N	\N
1308	1308	96	1	2026-10-08	purchase	\N	\N
1309	1309	96	1	2026-10-08	purchase	\N	\N
1310	1310	96	1	2026-10-08	donation	\N	\N
1311	1311	96	1	2026-10-08	purchase	\N	\N
1312	1312	96	1	2026-10-08	purchase	\N	\N
1313	1313	96	1	2026-10-08	purchase	\N	\N
1314	1314	96	1	2026-10-08	purchase	\N	\N
1315	1315	96	1	2026-10-08	purchase	\N	\N
1316	1316	96	1	2026-10-08	purchase	\N	\N
1317	1317	97	1	2026-10-08	purchase	\N	\N
1318	1318	97	1	2026-10-08	purchase	\N	\N
1319	1319	97	1	2026-10-08	donation	\N	\N
1320	1320	97	1	2026-10-08	purchase	\N	\N
1321	1321	97	1	2026-10-08	purchase	\N	\N
1322	1322	97	1	2026-10-08	purchase	\N	\N
1323	1323	97	1	2026-10-08	purchase	\N	\N
1324	1324	97	1	2026-10-08	purchase	\N	\N
1325	1325	97	1	2026-10-08	purchase	\N	\N
1326	1326	98	1	2026-10-08	purchase	\N	\N
1327	1327	98	1	2026-10-08	donation	\N	\N
1328	1328	98	1	2026-10-08	purchase	\N	\N
1329	1329	98	1	2026-10-08	purchase	\N	\N
1330	1330	98	1	2026-10-08	purchase	\N	\N
1331	1331	98	1	2026-10-08	purchase	\N	\N
1332	1332	98	1	2026-10-08	purchase	\N	\N
1333	1333	98	1	2026-10-08	purchase	\N	\N
1334	1334	98	1	2026-10-08	donation	\N	\N
1335	1335	98	1	2026-10-08	purchase	\N	\N
1336	1336	98	1	2026-10-08	purchase	\N	\N
1337	1337	98	1	2026-10-08	purchase	\N	\N
1338	1338	99	1	2026-10-08	donation	\N	\N
1339	1339	99	1	2026-10-08	purchase	\N	\N
1340	1340	99	1	2026-10-08	purchase	\N	\N
1341	1341	99	1	2026-10-08	purchase	\N	\N
1342	1342	99	1	2026-10-08	purchase	\N	\N
1343	1343	99	1	2026-10-08	purchase	\N	\N
1344	1344	99	1	2026-10-08	purchase	\N	\N
1345	1345	99	1	2026-10-08	donation	\N	\N
1346	1346	100	1	2026-10-08	purchase	\N	\N
1347	1347	101	1	2026-10-08	purchase	\N	\N
1348	1348	101	1	2026-10-08	purchase	\N	\N
1349	1349	101	1	2026-10-08	purchase	\N	\N
1350	1350	101	1	2026-10-08	purchase	\N	\N
1351	1351	101	1	2026-10-08	purchase	\N	\N
1352	1352	101	1	2026-10-08	donation	\N	\N
1353	1353	101	1	2026-10-08	purchase	\N	\N
1354	1354	101	1	2026-10-08	purchase	\N	\N
1355	1355	101	1	2026-10-08	purchase	\N	\N
1356	1356	101	1	2026-10-08	purchase	\N	\N
1357	1357	101	1	2026-10-08	purchase	\N	\N
1358	1358	101	1	2026-10-08	purchase	\N	\N
1359	1359	101	1	2026-10-08	donation	\N	\N
1360	1360	101	1	2026-10-08	purchase	\N	\N
1361	1361	101	1	2026-10-08	purchase	\N	\N
1362	1362	101	1	2026-10-08	purchase	\N	\N
1363	1363	101	1	2026-10-08	purchase	\N	\N
1364	1364	101	1	2026-10-08	purchase	\N	\N
1365	1365	101	1	2026-10-08	purchase	\N	\N
1366	1366	101	1	2026-10-08	donation	\N	\N
1367	1367	101	1	2026-10-08	purchase	\N	\N
1368	1368	101	1	2026-10-08	purchase	\N	\N
1369	1369	101	1	2026-10-08	purchase	\N	\N
1370	1370	101	1	2026-10-08	purchase	\N	\N
1371	1371	102	1	2026-10-08	purchase	\N	\N
1372	1372	102	1	2026-10-08	purchase	\N	\N
1373	1373	102	1	2026-10-08	purchase	\N	\N
1374	1374	102	1	2026-10-08	purchase	\N	\N
1375	1375	102	1	2026-10-08	donation	\N	\N
1376	1376	102	1	2026-10-08	purchase	\N	\N
1377	1377	102	1	2026-10-08	purchase	\N	\N
1378	1378	102	1	2026-10-08	purchase	\N	\N
1379	1379	102	1	2026-10-08	purchase	\N	\N
1380	1380	102	1	2026-10-08	purchase	\N	\N
1381	1381	102	1	2026-10-08	purchase	\N	\N
1382	1382	102	1	2026-10-08	donation	\N	\N
1383	1383	102	1	2026-10-08	purchase	\N	\N
1384	1384	102	1	2026-10-08	purchase	\N	\N
1385	1385	102	1	2026-10-08	purchase	\N	\N
1386	1386	102	1	2026-10-08	purchase	\N	\N
1387	1387	102	1	2026-10-08	purchase	\N	\N
1388	1388	102	1	2026-10-08	purchase	\N	\N
1389	1389	102	1	2026-10-08	donation	\N	\N
1390	1390	102	1	2026-10-08	purchase	\N	\N
1391	1391	102	1	2026-10-08	purchase	\N	\N
1392	1392	102	1	2026-10-08	purchase	\N	\N
1393	1393	103	1	2026-10-08	purchase	\N	\N
1394	1394	103	1	2026-10-08	purchase	\N	\N
1395	1395	103	1	2026-10-08	purchase	\N	\N
1396	1396	103	1	2026-10-08	donation	\N	\N
1397	1397	103	1	2026-10-08	purchase	\N	\N
1398	1398	103	1	2026-10-08	purchase	\N	\N
1399	1399	103	1	2026-10-08	purchase	\N	\N
1400	1400	103	1	2026-10-08	purchase	\N	\N
1401	1401	103	1	2026-10-08	purchase	\N	\N
1402	1402	103	1	2026-10-08	purchase	\N	\N
1403	1403	103	1	2026-10-08	donation	\N	\N
1404	1404	103	1	2026-10-08	purchase	\N	\N
1405	1405	103	1	2026-10-08	purchase	\N	\N
1406	1406	103	1	2026-10-08	purchase	\N	\N
1407	1407	103	1	2026-10-08	purchase	\N	\N
1408	1408	103	1	2026-10-08	purchase	\N	\N
1409	1409	103	1	2026-10-08	purchase	\N	\N
1410	1410	103	1	2026-10-08	donation	\N	\N
1411	1411	103	1	2026-10-08	purchase	\N	\N
1412	1412	103	1	2026-10-08	purchase	\N	\N
1413	1413	104	1	2026-10-08	purchase	\N	\N
1414	1414	104	1	2026-10-08	purchase	\N	\N
1415	1415	104	1	2026-10-08	donation	\N	\N
1416	1416	104	1	2026-10-08	purchase	\N	\N
1417	1417	104	1	2026-10-08	purchase	\N	\N
1418	1418	104	1	2026-10-08	purchase	\N	\N
1419	1419	104	1	2026-10-08	purchase	\N	\N
1420	1420	104	1	2026-10-08	purchase	\N	\N
1421	1421	104	1	2026-10-08	purchase	\N	\N
1422	1422	104	1	2026-10-08	donation	\N	\N
1423	1423	104	1	2026-10-08	purchase	\N	\N
1424	1424	104	1	2026-10-08	purchase	\N	\N
1425	1425	104	1	2026-10-08	purchase	\N	\N
1426	1426	104	1	2026-10-08	purchase	\N	\N
1427	1427	105	1	2026-10-08	purchase	\N	\N
1428	1428	105	1	2026-10-08	donation	\N	\N
1429	1429	105	1	2026-10-08	purchase	\N	\N
1430	1430	105	1	2026-10-08	purchase	\N	\N
1431	1431	105	1	2026-10-08	purchase	\N	\N
1432	1432	105	1	2026-10-08	purchase	\N	\N
1433	1433	105	1	2026-10-08	purchase	\N	\N
1434	1434	105	1	2026-10-08	purchase	\N	\N
1435	1435	105	1	2026-10-08	donation	\N	\N
1436	1436	105	1	2026-10-08	purchase	\N	\N
1437	1437	105	1	2026-10-08	purchase	\N	\N
1438	1438	105	1	2026-10-08	purchase	\N	\N
1439	1439	105	1	2026-10-08	purchase	\N	\N
1440	1440	105	1	2026-10-08	purchase	\N	\N
1441	1441	105	1	2026-10-08	purchase	\N	\N
1442	1442	105	1	2026-10-08	donation	\N	\N
1443	1443	105	1	2026-10-08	purchase	\N	\N
1444	1444	105	1	2026-10-08	purchase	\N	\N
1445	1445	105	1	2026-10-08	purchase	\N	\N
1446	1446	105	1	2026-10-08	purchase	\N	\N
1447	1447	106	1	2026-10-08	donation	\N	\N
1448	1448	106	1	2026-10-08	purchase	\N	\N
1449	1449	106	1	2026-10-08	purchase	\N	\N
1450	1450	106	1	2026-10-08	purchase	\N	\N
1451	1451	106	1	2026-10-08	purchase	\N	\N
1452	1452	106	1	2026-10-08	purchase	\N	\N
1453	1453	106	1	2026-10-08	purchase	\N	\N
1454	1454	106	1	2026-10-08	donation	\N	\N
1455	1455	106	1	2026-10-08	purchase	\N	\N
1456	1456	106	1	2026-10-08	purchase	\N	\N
1457	1457	106	1	2026-10-08	purchase	\N	\N
1458	1458	106	1	2026-10-08	purchase	\N	\N
1459	1459	106	1	2026-10-08	purchase	\N	\N
1460	1460	106	1	2026-10-08	purchase	\N	\N
1461	1461	106	1	2026-10-08	donation	\N	\N
1462	1462	106	1	2026-10-08	purchase	\N	\N
1463	1463	107	1	2026-10-08	purchase	\N	\N
1464	1464	107	1	2026-10-08	purchase	\N	\N
1465	1465	107	1	2026-10-08	purchase	\N	\N
1466	1466	107	1	2026-10-08	purchase	\N	\N
1467	1467	107	1	2026-10-08	purchase	\N	\N
1468	1468	107	1	2026-10-08	purchase	\N	\N
1469	1469	107	1	2026-10-08	donation	\N	\N
1470	1470	107	1	2026-10-08	purchase	\N	\N
1471	1471	107	1	2026-10-08	purchase	\N	\N
1472	1472	107	1	2026-10-08	purchase	\N	\N
1473	1473	107	1	2026-10-08	purchase	\N	\N
1474	1474	107	1	2026-10-08	purchase	\N	\N
1475	1475	107	1	2026-10-08	purchase	\N	\N
1476	1476	107	1	2026-10-08	donation	\N	\N
1477	1477	107	1	2026-10-08	purchase	\N	\N
1478	1478	107	1	2026-10-08	purchase	\N	\N
1479	1479	108	1	2026-10-08	purchase	\N	\N
1480	1480	108	1	2026-10-08	purchase	\N	\N
1481	1481	108	1	2026-10-08	purchase	\N	\N
1482	1482	108	1	2026-10-08	purchase	\N	\N
1483	1483	108	1	2026-10-08	purchase	\N	\N
1484	1484	108	1	2026-10-08	donation	\N	\N
1485	1485	108	1	2026-10-08	purchase	\N	\N
1486	1486	108	1	2026-10-08	purchase	\N	\N
1487	1487	108	1	2026-10-08	purchase	\N	\N
1488	1488	108	1	2026-10-08	purchase	\N	\N
1489	1489	108	1	2026-10-08	purchase	\N	\N
1490	1490	108	1	2026-10-08	purchase	\N	\N
1491	1491	108	1	2026-10-08	donation	\N	\N
1492	1492	108	1	2026-10-08	purchase	\N	\N
1493	1493	108	1	2026-10-08	purchase	\N	\N
1494	1494	108	1	2026-10-08	purchase	\N	\N
1495	1495	108	1	2026-10-08	purchase	\N	\N
1496	1496	108	1	2026-10-08	purchase	\N	\N
1497	1497	109	1	2026-10-08	purchase	\N	\N
1498	1498	109	1	2026-10-08	purchase	\N	\N
1499	1499	109	1	2026-10-08	purchase	\N	\N
1500	1500	109	1	2026-10-08	purchase	\N	\N
1501	1501	109	1	2026-10-08	donation	\N	\N
1502	1502	109	1	2026-10-08	purchase	\N	\N
1503	1503	109	1	2026-10-08	purchase	\N	\N
1504	1504	109	1	2026-10-08	purchase	\N	\N
1505	1505	109	1	2026-10-08	purchase	\N	\N
1506	1506	109	1	2026-10-08	purchase	\N	\N
1507	1507	109	1	2026-10-08	purchase	\N	\N
1508	1508	109	1	2026-10-08	donation	\N	\N
1509	1509	109	1	2026-10-08	purchase	\N	\N
1510	1510	109	1	2026-10-08	purchase	\N	\N
1511	1511	109	1	2026-10-08	purchase	\N	\N
1512	1512	109	1	2026-10-08	purchase	\N	\N
1513	1513	110	1	2026-10-08	purchase	\N	\N
1514	1514	110	1	2026-10-08	purchase	\N	\N
1515	1515	110	1	2026-10-08	purchase	\N	\N
1516	1516	110	1	2026-10-08	donation	\N	\N
1517	1517	110	1	2026-10-08	purchase	\N	\N
1518	1518	110	1	2026-10-08	purchase	\N	\N
1519	1519	110	1	2026-10-08	purchase	\N	\N
1520	1520	110	1	2026-10-08	purchase	\N	\N
1521	1521	110	1	2026-10-08	purchase	\N	\N
1522	1522	110	1	2026-10-08	purchase	\N	\N
1523	1523	110	1	2026-10-08	donation	\N	\N
1524	1524	110	1	2026-10-08	purchase	\N	\N
1525	1525	110	1	2026-10-08	purchase	\N	\N
1526	1526	110	1	2026-10-08	purchase	\N	\N
1527	1527	111	1	2026-10-08	purchase	\N	\N
1528	1528	111	1	2026-10-08	purchase	\N	\N
1529	1529	111	1	2026-10-08	donation	\N	\N
1530	1530	111	1	2026-10-08	purchase	\N	\N
1531	1531	111	1	2026-10-08	purchase	\N	\N
1532	1532	111	1	2026-10-08	purchase	\N	\N
1533	1533	111	1	2026-10-08	purchase	\N	\N
1534	1534	111	1	2026-10-08	purchase	\N	\N
1535	1535	111	1	2026-10-08	purchase	\N	\N
1536	1536	111	1	2026-10-08	donation	\N	\N
1537	1537	111	1	2026-10-08	purchase	\N	\N
1538	1538	111	1	2026-10-08	purchase	\N	\N
1539	1539	111	1	2026-10-08	purchase	\N	\N
1540	1540	111	1	2026-10-08	purchase	\N	\N
1541	1541	111	1	2026-10-08	purchase	\N	\N
1542	1542	111	1	2026-10-08	purchase	\N	\N
1543	1543	112	1	2026-10-08	purchase	\N	\N
1544	1544	112	1	2026-10-08	donation	\N	\N
1545	1545	112	1	2026-10-08	purchase	\N	\N
1546	1546	112	1	2026-10-08	purchase	\N	\N
1547	1547	112	1	2026-10-08	purchase	\N	\N
1548	1548	112	1	2026-10-08	purchase	\N	\N
1549	1549	112	1	2026-10-08	purchase	\N	\N
1550	1550	112	1	2026-10-08	purchase	\N	\N
1551	1551	112	1	2026-10-08	donation	\N	\N
1552	1552	112	1	2026-10-08	purchase	\N	\N
1553	1553	112	1	2026-10-08	purchase	\N	\N
1554	1554	112	1	2026-10-08	purchase	\N	\N
1555	1555	112	1	2026-10-08	purchase	\N	\N
1556	1556	112	1	2026-10-08	purchase	\N	\N
1557	1557	113	1	2026-10-08	donation	\N	\N
1558	1558	113	1	2026-10-08	purchase	\N	\N
1559	1559	113	1	2026-10-08	purchase	\N	\N
1560	1560	113	1	2026-10-08	purchase	\N	\N
1561	1561	113	1	2026-10-08	purchase	\N	\N
1562	1562	113	1	2026-10-08	purchase	\N	\N
1563	1563	113	1	2026-10-08	purchase	\N	\N
1564	1564	113	1	2026-10-08	donation	\N	\N
1565	1565	113	1	2026-10-08	purchase	\N	\N
1566	1566	113	1	2026-10-08	purchase	\N	\N
1567	1567	113	1	2026-10-08	purchase	\N	\N
1568	1568	113	1	2026-10-08	purchase	\N	\N
1569	1569	114	1	2026-10-08	purchase	\N	\N
1570	1570	114	1	2026-10-08	purchase	\N	\N
1571	1571	114	1	2026-10-08	purchase	\N	\N
1572	1572	114	1	2026-10-08	purchase	\N	\N
1573	1573	114	1	2026-10-08	purchase	\N	\N
1574	1574	114	1	2026-10-08	purchase	\N	\N
1575	1575	114	1	2026-10-08	donation	\N	\N
1576	1576	114	1	2026-10-08	purchase	\N	\N
1577	1577	114	1	2026-10-08	purchase	\N	\N
1578	1578	114	1	2026-10-08	purchase	\N	\N
1579	1579	114	1	2026-10-08	purchase	\N	\N
1580	1580	114	1	2026-10-08	purchase	\N	\N
1581	1581	114	1	2026-10-08	purchase	\N	\N
1582	1582	114	1	2026-10-08	donation	\N	\N
1583	1583	115	1	2026-10-08	purchase	\N	\N
1584	1584	115	1	2026-10-08	purchase	\N	\N
1585	1585	115	1	2026-10-08	purchase	\N	\N
1586	1586	115	1	2026-10-08	purchase	\N	\N
1587	1587	115	1	2026-10-08	purchase	\N	\N
1588	1588	115	1	2026-10-08	donation	\N	\N
1589	1589	115	1	2026-10-08	purchase	\N	\N
1590	1590	115	1	2026-10-08	purchase	\N	\N
1591	1591	115	1	2026-10-08	purchase	\N	\N
1592	1592	115	1	2026-10-08	purchase	\N	\N
1593	1593	115	1	2026-10-08	purchase	\N	\N
1594	1594	115	1	2026-10-08	purchase	\N	\N
1595	1595	115	1	2026-10-08	donation	\N	\N
1596	1596	115	1	2026-10-08	purchase	\N	\N
1597	1597	115	1	2026-10-08	purchase	\N	\N
1598	1598	115	1	2026-10-08	purchase	\N	\N
1599	1599	115	1	2026-10-08	purchase	\N	\N
1600	1600	115	1	2026-10-08	purchase	\N	\N
1601	1601	116	1	2026-10-08	purchase	\N	\N
1602	1602	116	1	2026-10-08	purchase	\N	\N
1603	1603	116	1	2026-10-08	purchase	\N	\N
1604	1604	116	1	2026-10-08	purchase	\N	\N
1605	1605	116	1	2026-10-08	donation	\N	\N
1606	1606	116	1	2026-10-08	purchase	\N	\N
1607	1607	116	1	2026-10-08	purchase	\N	\N
1608	1608	116	1	2026-10-08	purchase	\N	\N
1609	1609	116	1	2026-10-08	purchase	\N	\N
1610	1610	116	1	2026-10-08	purchase	\N	\N
1611	1611	116	1	2026-10-08	purchase	\N	\N
1612	1612	116	1	2026-10-08	donation	\N	\N
1613	1613	116	1	2026-10-08	purchase	\N	\N
1614	1614	116	1	2026-10-08	purchase	\N	\N
1615	1615	116	1	2026-10-08	purchase	\N	\N
1616	1616	116	1	2026-10-08	purchase	\N	\N
1617	1617	117	1	2026-10-08	purchase	\N	\N
1618	1618	117	1	2026-10-08	purchase	\N	\N
1619	1619	117	1	2026-10-08	purchase	\N	\N
1620	1620	117	1	2026-10-08	donation	\N	\N
1621	1621	117	1	2026-10-08	purchase	\N	\N
1622	1622	117	1	2026-10-08	purchase	\N	\N
1623	1623	117	1	2026-10-08	purchase	\N	\N
1624	1624	117	1	2026-10-08	purchase	\N	\N
1625	1625	117	1	2026-10-08	purchase	\N	\N
1626	1626	117	1	2026-10-08	purchase	\N	\N
1627	1627	117	1	2026-10-08	donation	\N	\N
1628	1628	117	1	2026-10-08	purchase	\N	\N
1629	1629	117	1	2026-10-08	purchase	\N	\N
1630	1630	117	1	2026-10-08	purchase	\N	\N
1631	1631	117	1	2026-10-08	purchase	\N	\N
1632	1632	118	1	2026-10-08	purchase	\N	\N
1633	1633	118	1	2026-10-08	purchase	\N	\N
1634	1634	118	1	2026-10-08	donation	\N	\N
1635	1635	118	1	2026-10-08	purchase	\N	\N
1636	1636	118	1	2026-10-08	purchase	\N	\N
1637	1637	118	1	2026-10-08	purchase	\N	\N
1638	1638	118	1	2026-10-08	purchase	\N	\N
1639	1639	118	1	2026-10-08	purchase	\N	\N
1640	1640	118	1	2026-10-08	purchase	\N	\N
1641	1641	118	1	2026-10-08	donation	\N	\N
1642	1642	118	1	2026-10-08	purchase	\N	\N
1643	1643	118	1	2026-10-08	purchase	\N	\N
1644	1644	118	1	2026-10-08	purchase	\N	\N
1645	1645	118	1	2026-10-08	purchase	\N	\N
1646	1646	118	1	2026-10-08	purchase	\N	\N
1647	1647	118	1	2026-10-08	purchase	\N	\N
1648	1648	118	1	2026-10-08	donation	\N	\N
1649	1649	119	1	2026-10-08	purchase	\N	\N
1650	1650	119	1	2026-10-08	donation	\N	\N
1651	1651	119	1	2026-10-08	purchase	\N	\N
1652	1652	119	1	2026-10-08	purchase	\N	\N
1653	1653	119	1	2026-10-08	purchase	\N	\N
1654	1654	119	1	2026-10-08	purchase	\N	\N
1655	1655	119	1	2026-10-08	purchase	\N	\N
1656	1656	119	1	2026-10-08	purchase	\N	\N
1657	1657	119	1	2026-10-08	donation	\N	\N
1658	1658	119	1	2026-10-08	purchase	\N	\N
1659	1659	119	1	2026-10-08	purchase	\N	\N
1660	1660	119	1	2026-10-08	purchase	\N	\N
1661	1661	119	1	2026-10-08	purchase	\N	\N
1662	1662	120	1	2026-10-08	donation	\N	\N
1663	1663	120	1	2026-10-08	purchase	\N	\N
1664	1664	120	1	2026-10-08	purchase	\N	\N
1665	1665	120	1	2026-10-08	purchase	\N	\N
1666	1666	120	1	2026-10-08	purchase	\N	\N
1667	1667	120	1	2026-10-08	purchase	\N	\N
1668	1668	120	1	2026-10-08	purchase	\N	\N
1669	1669	120	1	2026-10-08	donation	\N	\N
1670	1670	120	1	2026-10-08	purchase	\N	\N
1671	1671	120	1	2026-10-08	purchase	\N	\N
1672	1672	120	1	2026-10-08	purchase	\N	\N
1673	1673	121	1	2026-10-08	purchase	\N	\N
1674	1674	121	1	2026-10-08	purchase	\N	\N
1675	1675	121	1	2026-10-08	purchase	\N	\N
1676	1676	121	1	2026-10-08	purchase	\N	\N
1677	1677	121	1	2026-10-08	purchase	\N	\N
1678	1678	121	1	2026-10-08	purchase	\N	\N
1679	1679	121	1	2026-10-08	donation	\N	\N
1680	1680	121	1	2026-10-08	purchase	\N	\N
1681	1681	121	1	2026-10-08	purchase	\N	\N
1682	1682	121	1	2026-10-08	purchase	\N	\N
1683	1683	121	1	2026-10-08	purchase	\N	\N
1684	1684	121	1	2026-10-08	purchase	\N	\N
1685	1685	121	1	2026-10-08	purchase	\N	\N
1686	1686	122	1	2026-10-08	purchase	\N	\N
1687	1687	122	1	2026-10-08	purchase	\N	\N
1688	1688	122	1	2026-10-08	purchase	\N	\N
1689	1689	122	1	2026-10-08	purchase	\N	\N
1690	1690	122	1	2026-10-08	purchase	\N	\N
1691	1691	122	1	2026-10-08	donation	\N	\N
1692	1692	122	1	2026-10-08	purchase	\N	\N
1693	1693	122	1	2026-10-08	purchase	\N	\N
1694	1694	122	1	2026-10-08	purchase	\N	\N
1695	1695	122	1	2026-10-08	purchase	\N	\N
1696	1696	122	1	2026-10-08	purchase	\N	\N
1697	1697	122	1	2026-10-08	purchase	\N	\N
1698	1698	122	1	2026-10-08	donation	\N	\N
1699	1699	123	1	2026-10-08	purchase	\N	\N
1700	1700	123	1	2026-10-08	purchase	\N	\N
1701	1701	123	1	2026-10-08	purchase	\N	\N
1702	1702	123	1	2026-10-08	purchase	\N	\N
1703	1703	123	1	2026-10-08	donation	\N	\N
1704	1704	123	1	2026-10-08	purchase	\N	\N
1705	1705	123	1	2026-10-08	purchase	\N	\N
1706	1706	123	1	2026-10-08	purchase	\N	\N
1707	1707	123	1	2026-10-08	purchase	\N	\N
1708	1708	123	1	2026-10-08	purchase	\N	\N
1709	1709	123	1	2026-10-08	purchase	\N	\N
1710	1710	124	1	2026-10-08	purchase	\N	\N
1711	1711	124	1	2026-10-08	purchase	\N	\N
1712	1712	124	1	2026-10-08	purchase	\N	\N
1713	1713	124	1	2026-10-08	donation	\N	\N
1714	1714	124	1	2026-10-08	purchase	\N	\N
1715	1715	124	1	2026-10-08	purchase	\N	\N
1716	1716	124	1	2026-10-08	purchase	\N	\N
1717	1717	124	1	2026-10-08	purchase	\N	\N
1718	1718	124	1	2026-10-08	purchase	\N	\N
1719	1719	125	1	2026-10-08	purchase	\N	\N
1720	1720	125	1	2026-10-08	purchase	\N	\N
1721	1721	125	1	2026-10-08	donation	\N	\N
1722	1722	125	1	2026-10-08	purchase	\N	\N
1723	1723	125	1	2026-10-08	purchase	\N	\N
1724	1724	125	1	2026-10-08	purchase	\N	\N
1725	1725	125	1	2026-10-08	purchase	\N	\N
1726	1726	125	1	2026-10-08	purchase	\N	\N
1727	1727	125	1	2026-10-08	purchase	\N	\N
1728	1728	125	1	2026-10-08	donation	\N	\N
1729	1729	125	1	2026-10-08	purchase	\N	\N
1730	1730	126	1	2026-10-08	purchase	\N	\N
1731	1731	126	1	2026-10-08	donation	\N	\N
1732	1732	126	1	2026-10-08	purchase	\N	\N
1733	1733	126	1	2026-10-08	purchase	\N	\N
1734	1734	126	1	2026-10-08	purchase	\N	\N
1735	1735	126	1	2026-10-08	purchase	\N	\N
1736	1736	126	1	2026-10-08	purchase	\N	\N
1737	1737	126	1	2026-10-08	purchase	\N	\N
1738	1738	127	1	2026-10-08	donation	\N	\N
1739	1739	127	1	2026-10-08	purchase	\N	\N
1740	1740	127	1	2026-10-08	purchase	\N	\N
1741	1741	127	1	2026-10-08	purchase	\N	\N
1742	1742	127	1	2026-10-08	purchase	\N	\N
1743	1743	127	1	2026-10-08	purchase	\N	\N
1744	1744	127	1	2026-10-08	purchase	\N	\N
1745	1745	127	1	2026-10-08	donation	\N	\N
1746	1746	127	1	2026-10-08	purchase	\N	\N
1747	1747	127	1	2026-10-08	purchase	\N	\N
1748	1748	127	1	2026-10-08	purchase	\N	\N
1749	1749	128	1	2026-10-08	purchase	\N	\N
1750	1750	128	1	2026-10-08	purchase	\N	\N
1751	1751	128	1	2026-10-08	purchase	\N	\N
1752	1752	128	1	2026-10-08	purchase	\N	\N
1753	1753	128	1	2026-10-08	purchase	\N	\N
1754	1754	128	1	2026-10-08	purchase	\N	\N
1755	1755	128	1	2026-10-08	donation	\N	\N
1756	1756	128	1	2026-10-08	purchase	\N	\N
1757	1757	128	1	2026-10-08	purchase	\N	\N
1758	1758	128	1	2026-10-08	purchase	\N	\N
1759	1759	128	1	2026-10-08	purchase	\N	\N
1760	1760	128	1	2026-10-08	purchase	\N	\N
1761	1761	128	1	2026-10-08	purchase	\N	\N
1762	1762	129	1	2026-10-08	purchase	\N	\N
1763	1763	129	1	2026-10-08	purchase	\N	\N
1764	1764	129	1	2026-10-08	purchase	\N	\N
1765	1765	129	1	2026-10-08	purchase	\N	\N
1766	1766	129	1	2026-10-08	purchase	\N	\N
1767	1767	129	1	2026-10-08	donation	\N	\N
1768	1768	129	1	2026-10-08	purchase	\N	\N
1769	1769	129	1	2026-10-08	purchase	\N	\N
1770	1770	129	1	2026-10-08	purchase	\N	\N
1771	1771	129	1	2026-10-08	purchase	\N	\N
1772	1772	129	1	2026-10-08	purchase	\N	\N
1773	1773	130	1	2026-10-08	purchase	\N	\N
1774	1774	130	1	2026-10-08	purchase	\N	\N
1775	1775	130	1	2026-10-08	purchase	\N	\N
1776	1776	130	1	2026-10-08	purchase	\N	\N
1777	1777	130	1	2026-10-08	donation	\N	\N
1778	1778	130	1	2026-10-08	purchase	\N	\N
1779	1779	130	1	2026-10-08	purchase	\N	\N
1780	1780	130	1	2026-10-08	purchase	\N	\N
1781	1781	130	1	2026-10-08	purchase	\N	\N
1782	1782	130	1	2026-10-08	purchase	\N	\N
1783	1783	130	1	2026-10-08	purchase	\N	\N
1784	1784	131	1	2026-10-08	purchase	\N	\N
1785	1785	131	1	2026-10-08	purchase	\N	\N
1786	1786	131	1	2026-10-08	purchase	\N	\N
1787	1787	131	1	2026-10-08	donation	\N	\N
1788	1788	131	1	2026-10-08	purchase	\N	\N
1789	1789	131	1	2026-10-08	purchase	\N	\N
1790	1790	131	1	2026-10-08	purchase	\N	\N
1791	1791	131	1	2026-10-08	purchase	\N	\N
1792	1792	131	1	2026-10-08	purchase	\N	\N
1793	1793	132	1	2026-10-08	purchase	\N	\N
1794	1794	132	1	2026-10-08	purchase	\N	\N
1795	1795	132	1	2026-10-08	donation	\N	\N
1796	1796	132	1	2026-10-08	purchase	\N	\N
1797	1797	132	1	2026-10-08	purchase	\N	\N
1798	1798	132	1	2026-10-08	purchase	\N	\N
1799	1799	132	1	2026-10-08	purchase	\N	\N
1800	1800	132	1	2026-10-08	purchase	\N	\N
1801	1801	133	1	2026-10-08	purchase	\N	\N
1802	1802	133	1	2026-10-08	donation	\N	\N
1803	1803	133	1	2026-10-08	purchase	\N	\N
1804	1804	133	1	2026-10-08	purchase	\N	\N
1805	1805	133	1	2026-10-08	purchase	\N	\N
1806	1806	133	1	2026-10-08	purchase	\N	\N
1807	1807	133	1	2026-10-08	purchase	\N	\N
1808	1808	133	1	2026-10-08	purchase	\N	\N
1809	1809	133	1	2026-10-08	donation	\N	\N
1810	1810	134	1	2026-10-08	donation	\N	\N
1811	1811	134	1	2026-10-08	purchase	\N	\N
1812	1812	134	1	2026-10-08	purchase	\N	\N
1813	1813	134	1	2026-10-08	purchase	\N	\N
1814	1814	134	1	2026-10-08	purchase	\N	\N
1815	1815	134	1	2026-10-08	purchase	\N	\N
1816	1816	134	1	2026-10-08	purchase	\N	\N
1817	1817	134	1	2026-10-08	donation	\N	\N
1818	1818	134	1	2026-10-08	purchase	\N	\N
1819	1819	134	1	2026-10-08	purchase	\N	\N
1820	1820	134	1	2026-10-08	purchase	\N	\N
1821	1821	135	1	2026-10-08	purchase	\N	\N
1822	1822	135	1	2026-10-08	purchase	\N	\N
1823	1823	135	1	2026-10-08	purchase	\N	\N
1824	1824	135	1	2026-10-08	purchase	\N	\N
1825	1825	135	1	2026-10-08	purchase	\N	\N
1826	1826	135	1	2026-10-08	purchase	\N	\N
1827	1827	135	1	2026-10-08	donation	\N	\N
1828	1828	135	1	2026-10-08	purchase	\N	\N
1829	1829	135	1	2026-10-08	purchase	\N	\N
1830	1830	135	1	2026-10-08	purchase	\N	\N
1831	1831	135	1	2026-10-08	purchase	\N	\N
1832	1832	136	1	2026-10-08	purchase	\N	\N
1833	1833	136	1	2026-10-08	purchase	\N	\N
1834	1834	136	1	2026-10-08	purchase	\N	\N
1835	1835	136	1	2026-10-08	purchase	\N	\N
1836	1836	136	1	2026-10-08	purchase	\N	\N
1837	1837	136	1	2026-10-08	donation	\N	\N
1838	1838	136	1	2026-10-08	purchase	\N	\N
1839	1839	136	1	2026-10-08	purchase	\N	\N
1840	1840	136	1	2026-10-08	purchase	\N	\N
1841	1841	137	1	2026-10-08	purchase	\N	\N
1842	1842	137	1	2026-10-08	purchase	\N	\N
1843	1843	137	1	2026-10-08	purchase	\N	\N
1844	1844	137	1	2026-10-08	purchase	\N	\N
1845	1845	137	1	2026-10-08	donation	\N	\N
1846	1846	137	1	2026-10-08	purchase	\N	\N
1847	1847	137	1	2026-10-08	purchase	\N	\N
1848	1848	138	1	2026-10-08	purchase	\N	\N
1849	1849	138	1	2026-10-08	purchase	\N	\N
1850	1850	138	1	2026-10-08	purchase	\N	\N
1851	1851	138	1	2026-10-08	donation	\N	\N
1852	1852	138	1	2026-10-08	purchase	\N	\N
1853	1853	138	1	2026-10-08	purchase	\N	\N
1854	1854	138	1	2026-10-08	purchase	\N	\N
1855	1855	138	1	2026-10-08	purchase	\N	\N
1856	1856	139	1	2026-10-08	purchase	\N	\N
1857	1857	139	1	2026-10-08	purchase	\N	\N
1858	1858	139	1	2026-10-08	donation	\N	\N
1859	1859	139	1	2026-10-08	purchase	\N	\N
1860	1860	139	1	2026-10-08	purchase	\N	\N
1861	1861	139	1	2026-10-08	purchase	\N	\N
1862	1862	139	1	2026-10-08	purchase	\N	\N
1863	1863	139	1	2026-10-08	purchase	\N	\N
1864	1864	140	1	2026-10-08	purchase	\N	\N
1865	1865	140	1	2026-10-08	donation	\N	\N
1866	1866	140	1	2026-10-08	purchase	\N	\N
1867	1867	140	1	2026-10-08	purchase	\N	\N
1868	1868	140	1	2026-10-08	purchase	\N	\N
1869	1869	140	1	2026-10-08	purchase	\N	\N
1870	1870	140	1	2026-10-08	purchase	\N	\N
1871	1871	141	1	2026-10-08	donation	\N	\N
1872	1872	141	1	2026-10-08	purchase	\N	\N
1873	1873	141	1	2026-10-08	purchase	\N	\N
1874	1874	141	1	2026-10-08	purchase	\N	\N
1875	1875	141	1	2026-10-08	purchase	\N	\N
1876	1876	141	1	2026-10-08	purchase	\N	\N
1877	1877	141	1	2026-10-08	purchase	\N	\N
1878	1878	142	1	2026-10-08	purchase	\N	\N
1879	1879	142	1	2026-10-08	purchase	\N	\N
1880	1880	142	1	2026-10-08	purchase	\N	\N
1881	1881	142	1	2026-10-08	purchase	\N	\N
1882	1882	142	1	2026-10-08	purchase	\N	\N
1883	1883	142	1	2026-10-08	purchase	\N	\N
1884	1884	142	1	2026-10-08	donation	\N	\N
1885	1885	143	1	2026-10-08	purchase	\N	\N
1886	1886	143	1	2026-10-08	purchase	\N	\N
1887	1887	143	1	2026-10-08	purchase	\N	\N
1888	1888	143	1	2026-10-08	purchase	\N	\N
1889	1889	143	1	2026-10-08	purchase	\N	\N
1890	1890	143	1	2026-10-08	donation	\N	\N
1891	1891	144	1	2026-10-08	purchase	\N	\N
1892	1892	144	1	2026-10-08	purchase	\N	\N
1893	1893	144	1	2026-10-08	purchase	\N	\N
1894	1894	144	1	2026-10-08	purchase	\N	\N
1895	1895	144	1	2026-10-08	donation	\N	\N
1896	1896	144	1	2026-10-08	purchase	\N	\N
1897	1897	144	1	2026-10-08	purchase	\N	\N
1898	1898	144	1	2026-10-08	purchase	\N	\N
1899	1899	145	1	2026-10-08	purchase	\N	\N
1900	1900	145	1	2026-10-08	purchase	\N	\N
1901	1901	145	1	2026-10-08	purchase	\N	\N
1902	1902	145	1	2026-10-08	donation	\N	\N
1903	1903	145	1	2026-10-08	purchase	\N	\N
1904	1904	145	1	2026-10-08	purchase	\N	\N
1905	1905	145	1	2026-10-08	purchase	\N	\N
1906	1906	145	1	2026-10-08	purchase	\N	\N
1907	1907	145	1	2026-10-08	purchase	\N	\N
1908	1908	145	1	2026-10-08	purchase	\N	\N
1909	1909	145	1	2026-10-08	donation	\N	\N
1910	1910	146	1	2026-10-08	purchase	\N	\N
1911	1911	146	1	2026-10-08	purchase	\N	\N
1912	1912	146	1	2026-10-08	donation	\N	\N
1913	1913	146	1	2026-10-08	purchase	\N	\N
1914	1914	146	1	2026-10-08	purchase	\N	\N
1915	1915	146	1	2026-10-08	purchase	\N	\N
1916	1916	146	1	2026-10-08	purchase	\N	\N
1917	1917	146	1	2026-10-08	purchase	\N	\N
1918	1918	146	1	2026-10-08	purchase	\N	\N
1919	1919	146	1	2026-10-08	donation	\N	\N
1920	1920	146	1	2026-10-08	purchase	\N	\N
1921	1921	146	1	2026-10-08	purchase	\N	\N
1922	1922	146	1	2026-10-08	purchase	\N	\N
1923	1923	147	1	2026-10-08	purchase	\N	\N
1924	1924	147	1	2026-10-08	donation	\N	\N
1925	1925	147	1	2026-10-08	purchase	\N	\N
1926	1926	147	1	2026-10-08	purchase	\N	\N
1927	1927	147	1	2026-10-08	purchase	\N	\N
1928	1928	147	1	2026-10-08	purchase	\N	\N
1929	1929	147	1	2026-10-08	purchase	\N	\N
1930	1930	147	1	2026-10-08	purchase	\N	\N
1931	1931	147	1	2026-10-08	donation	\N	\N
1932	1932	147	1	2026-10-08	purchase	\N	\N
1933	1933	147	1	2026-10-08	purchase	\N	\N
1934	1934	148	1	2026-10-08	donation	\N	\N
1935	1935	149	1	2026-10-08	purchase	\N	\N
1936	1936	149	1	2026-10-08	purchase	\N	\N
1937	1937	149	1	2026-10-08	purchase	\N	\N
1938	1938	149	1	2026-10-08	purchase	\N	\N
1939	1939	149	1	2026-10-08	purchase	\N	\N
1940	1940	149	1	2026-10-08	purchase	\N	\N
1941	1941	149	1	2026-10-08	donation	\N	\N
1942	1942	149	1	2026-10-08	purchase	\N	\N
1943	1943	149	1	2026-10-08	purchase	\N	\N
1944	1944	149	1	2026-10-08	purchase	\N	\N
1945	1945	149	1	2026-10-08	purchase	\N	\N
1946	1946	149	1	2026-10-08	purchase	\N	\N
1947	1947	149	1	2026-10-08	purchase	\N	\N
1948	1948	149	1	2026-10-08	donation	\N	\N
1949	1949	149	1	2026-10-08	purchase	\N	\N
1950	1950	149	1	2026-10-08	purchase	\N	\N
1951	1951	149	1	2026-10-08	purchase	\N	\N
1952	1952	149	1	2026-10-08	purchase	\N	\N
1953	1953	149	1	2026-10-08	purchase	\N	\N
1954	1954	149	1	2026-10-08	purchase	\N	\N
1955	1955	149	1	2026-10-08	donation	\N	\N
1956	1956	149	1	2026-10-08	purchase	\N	\N
1957	1957	149	1	2026-10-08	purchase	\N	\N
1958	1958	150	1	2026-10-08	purchase	\N	\N
1959	1959	150	1	2026-10-08	purchase	\N	\N
1960	1960	150	1	2026-10-08	purchase	\N	\N
1961	1961	150	1	2026-10-08	purchase	\N	\N
1962	1962	150	1	2026-10-08	purchase	\N	\N
1963	1963	150	1	2026-10-08	donation	\N	\N
1964	1964	150	1	2026-10-08	purchase	\N	\N
1965	1965	150	1	2026-10-08	purchase	\N	\N
1966	1966	150	1	2026-10-08	purchase	\N	\N
1967	1967	150	1	2026-10-08	purchase	\N	\N
1968	1968	150	1	2026-10-08	purchase	\N	\N
1969	1969	150	1	2026-10-08	purchase	\N	\N
1970	1970	150	1	2026-10-08	donation	\N	\N
1971	1971	150	1	2026-10-08	purchase	\N	\N
1972	1972	150	1	2026-10-08	purchase	\N	\N
1973	1973	150	1	2026-10-08	purchase	\N	\N
1974	1974	150	1	2026-10-08	purchase	\N	\N
1975	1975	150	1	2026-10-08	purchase	\N	\N
1976	1976	150	1	2026-10-08	purchase	\N	\N
1977	1977	150	1	2026-10-08	donation	\N	\N
1978	1978	150	1	2026-10-08	purchase	\N	\N
1979	1979	151	1	2026-10-08	purchase	\N	\N
1980	1980	151	1	2026-10-08	purchase	\N	\N
1981	1981	151	1	2026-10-08	purchase	\N	\N
1982	1982	151	1	2026-10-08	purchase	\N	\N
1983	1983	151	1	2026-10-08	donation	\N	\N
1984	1984	151	1	2026-10-08	purchase	\N	\N
1985	1985	151	1	2026-10-08	purchase	\N	\N
1986	1986	151	1	2026-10-08	purchase	\N	\N
1987	1987	151	1	2026-10-08	purchase	\N	\N
1988	1988	151	1	2026-10-08	purchase	\N	\N
1989	1989	151	1	2026-10-08	purchase	\N	\N
1990	1990	151	1	2026-10-08	donation	\N	\N
1991	1991	151	1	2026-10-08	purchase	\N	\N
1992	1992	151	1	2026-10-08	purchase	\N	\N
1993	1993	151	1	2026-10-08	purchase	\N	\N
1994	1994	151	1	2026-10-08	purchase	\N	\N
1995	1995	151	1	2026-10-08	purchase	\N	\N
1996	1996	151	1	2026-10-08	purchase	\N	\N
1997	1997	151	1	2026-10-08	donation	\N	\N
1998	1998	151	1	2026-10-08	purchase	\N	\N
1999	1999	151	1	2026-10-08	purchase	\N	\N
2000	2000	151	1	2026-10-08	purchase	\N	\N
2001	2001	151	1	2026-10-08	purchase	\N	\N
2002	2002	152	1	2026-10-08	purchase	\N	\N
2003	2003	152	1	2026-10-08	purchase	\N	\N
2004	2004	152	1	2026-10-08	purchase	\N	\N
2005	2005	152	1	2026-10-08	donation	\N	\N
2006	2006	152	1	2026-10-08	purchase	\N	\N
2007	2007	152	1	2026-10-08	purchase	\N	\N
2008	2008	152	1	2026-10-08	purchase	\N	\N
2009	2009	152	1	2026-10-08	purchase	\N	\N
2010	2010	152	1	2026-10-08	purchase	\N	\N
2011	2011	152	1	2026-10-08	purchase	\N	\N
2012	2012	152	1	2026-10-08	donation	\N	\N
2013	2013	152	1	2026-10-08	purchase	\N	\N
2014	2014	152	1	2026-10-08	purchase	\N	\N
2015	2015	152	1	2026-10-08	purchase	\N	\N
2016	2016	152	1	2026-10-08	purchase	\N	\N
2017	2017	152	1	2026-10-08	purchase	\N	\N
2018	2018	152	1	2026-10-08	purchase	\N	\N
2019	2019	152	1	2026-10-08	donation	\N	\N
2020	2020	152	1	2026-10-08	purchase	\N	\N
2021	2021	152	1	2026-10-08	purchase	\N	\N
2022	2022	152	1	2026-10-08	purchase	\N	\N
2023	2023	153	1	2026-10-08	purchase	\N	\N
2024	2024	153	1	2026-10-08	purchase	\N	\N
2025	2025	153	1	2026-10-08	donation	\N	\N
2026	2026	153	1	2026-10-08	purchase	\N	\N
2027	2027	153	1	2026-10-08	purchase	\N	\N
2028	2028	153	1	2026-10-08	purchase	\N	\N
2029	2029	153	1	2026-10-08	purchase	\N	\N
2030	2030	153	1	2026-10-08	purchase	\N	\N
2031	2031	153	1	2026-10-08	purchase	\N	\N
2032	2032	153	1	2026-10-08	donation	\N	\N
2033	2033	153	1	2026-10-08	purchase	\N	\N
2034	2034	153	1	2026-10-08	purchase	\N	\N
2035	2035	153	1	2026-10-08	purchase	\N	\N
2036	2036	153	1	2026-10-08	purchase	\N	\N
2037	2037	153	1	2026-10-08	purchase	\N	\N
2038	2038	153	1	2026-10-08	purchase	\N	\N
2039	2039	153	1	2026-10-08	donation	\N	\N
2040	2040	153	1	2026-10-08	purchase	\N	\N
2041	2041	153	1	2026-10-08	purchase	\N	\N
2042	2042	154	1	2026-10-08	purchase	\N	\N
2043	2043	154	1	2026-10-08	donation	\N	\N
2044	2044	154	1	2026-10-08	purchase	\N	\N
2045	2045	154	1	2026-10-08	purchase	\N	\N
2046	2046	154	1	2026-10-08	purchase	\N	\N
2047	2047	154	1	2026-10-08	purchase	\N	\N
2048	2048	154	1	2026-10-08	purchase	\N	\N
2049	2049	154	1	2026-10-08	purchase	\N	\N
2050	2050	154	1	2026-10-08	donation	\N	\N
2051	2051	154	1	2026-10-08	purchase	\N	\N
2052	2052	154	1	2026-10-08	purchase	\N	\N
2053	2053	154	1	2026-10-08	purchase	\N	\N
2054	2054	154	1	2026-10-08	purchase	\N	\N
2055	2055	154	1	2026-10-08	purchase	\N	\N
2056	2056	154	1	2026-10-08	purchase	\N	\N
2057	2057	154	1	2026-10-08	donation	\N	\N
2058	2058	154	1	2026-10-08	purchase	\N	\N
2059	2059	155	1	2026-10-08	donation	\N	\N
2060	2060	155	1	2026-10-08	purchase	\N	\N
2061	2061	155	1	2026-10-08	purchase	\N	\N
2062	2062	155	1	2026-10-08	purchase	\N	\N
2063	2063	155	1	2026-10-08	purchase	\N	\N
2064	2064	155	1	2026-10-08	purchase	\N	\N
2065	2065	155	1	2026-10-08	purchase	\N	\N
2066	2066	155	1	2026-10-08	donation	\N	\N
2067	2067	155	1	2026-10-08	purchase	\N	\N
2068	2068	155	1	2026-10-08	purchase	\N	\N
2069	2069	155	1	2026-10-08	purchase	\N	\N
2070	2070	155	1	2026-10-08	purchase	\N	\N
2071	2071	155	1	2026-10-08	purchase	\N	\N
2072	2072	155	1	2026-10-08	purchase	\N	\N
2073	2073	155	1	2026-10-08	donation	\N	\N
2074	2074	155	1	2026-10-08	purchase	\N	\N
2075	2075	155	1	2026-10-08	purchase	\N	\N
2076	2076	156	1	2026-10-08	purchase	\N	\N
2077	2077	156	1	2026-10-08	purchase	\N	\N
2078	2078	156	1	2026-10-08	purchase	\N	\N
2079	2079	156	1	2026-10-08	purchase	\N	\N
2080	2080	156	1	2026-10-08	purchase	\N	\N
2081	2081	156	1	2026-10-08	purchase	\N	\N
2082	2082	156	1	2026-10-08	donation	\N	\N
2083	2083	156	1	2026-10-08	purchase	\N	\N
2084	2084	156	1	2026-10-08	purchase	\N	\N
2085	2085	156	1	2026-10-08	purchase	\N	\N
2086	2086	156	1	2026-10-08	purchase	\N	\N
2087	2087	156	1	2026-10-08	purchase	\N	\N
2088	2088	156	1	2026-10-08	purchase	\N	\N
2089	2089	156	1	2026-10-08	donation	\N	\N
2090	2090	156	1	2026-10-08	purchase	\N	\N
2091	2091	156	1	2026-10-08	purchase	\N	\N
2092	2092	156	1	2026-10-08	purchase	\N	\N
2093	2093	156	1	2026-10-08	purchase	\N	\N
2094	2094	156	1	2026-10-08	purchase	\N	\N
2095	2095	157	1	2026-10-08	purchase	\N	\N
2096	2096	157	1	2026-10-08	purchase	\N	\N
2097	2097	157	1	2026-10-08	purchase	\N	\N
2098	2098	157	1	2026-10-08	purchase	\N	\N
2099	2099	157	1	2026-10-08	purchase	\N	\N
2100	2100	157	1	2026-10-08	donation	\N	\N
2101	2101	157	1	2026-10-08	purchase	\N	\N
2102	2102	157	1	2026-10-08	purchase	\N	\N
2103	2103	157	1	2026-10-08	purchase	\N	\N
2104	2104	157	1	2026-10-08	purchase	\N	\N
2105	2105	157	1	2026-10-08	purchase	\N	\N
2106	2106	157	1	2026-10-08	purchase	\N	\N
2107	2107	157	1	2026-10-08	donation	\N	\N
2108	2108	157	1	2026-10-08	purchase	\N	\N
2109	2109	157	1	2026-10-08	purchase	\N	\N
2110	2110	158	1	2026-10-08	purchase	\N	\N
2111	2111	158	1	2026-10-08	purchase	\N	\N
2112	2112	158	1	2026-10-08	purchase	\N	\N
2113	2113	158	1	2026-10-08	purchase	\N	\N
2114	2114	158	1	2026-10-08	donation	\N	\N
2115	2115	158	1	2026-10-08	purchase	\N	\N
2116	2116	158	1	2026-10-08	purchase	\N	\N
2117	2117	158	1	2026-10-08	purchase	\N	\N
2118	2118	158	1	2026-10-08	purchase	\N	\N
2119	2119	158	1	2026-10-08	purchase	\N	\N
2120	2120	158	1	2026-10-08	purchase	\N	\N
2121	2121	158	1	2026-10-08	donation	\N	\N
2122	2122	158	1	2026-10-08	purchase	\N	\N
2123	2123	158	1	2026-10-08	purchase	\N	\N
2124	2124	158	1	2026-10-08	purchase	\N	\N
2125	2125	158	1	2026-10-08	purchase	\N	\N
2126	2126	158	1	2026-10-08	purchase	\N	\N
2127	2127	158	1	2026-10-08	purchase	\N	\N
2128	2128	158	1	2026-10-08	donation	\N	\N
2129	2129	159	1	2026-10-08	purchase	\N	\N
2130	2130	159	1	2026-10-08	purchase	\N	\N
2131	2131	159	1	2026-10-08	purchase	\N	\N
2132	2132	159	1	2026-10-08	donation	\N	\N
2133	2133	159	1	2026-10-08	purchase	\N	\N
2134	2134	159	1	2026-10-08	purchase	\N	\N
2135	2135	159	1	2026-10-08	purchase	\N	\N
2136	2136	159	1	2026-10-08	purchase	\N	\N
2137	2137	159	1	2026-10-08	purchase	\N	\N
2138	2138	159	1	2026-10-08	purchase	\N	\N
2139	2139	159	1	2026-10-08	donation	\N	\N
2140	2140	159	1	2026-10-08	purchase	\N	\N
2141	2141	159	1	2026-10-08	purchase	\N	\N
2142	2142	159	1	2026-10-08	purchase	\N	\N
2143	2143	159	1	2026-10-08	purchase	\N	\N
2144	2144	159	1	2026-10-08	purchase	\N	\N
2145	2145	159	1	2026-10-08	purchase	\N	\N
2146	2146	160	1	2026-10-08	purchase	\N	\N
2147	2147	160	1	2026-10-08	purchase	\N	\N
2148	2148	160	1	2026-10-08	donation	\N	\N
2149	2149	160	1	2026-10-08	purchase	\N	\N
2150	2150	160	1	2026-10-08	purchase	\N	\N
2151	2151	160	1	2026-10-08	purchase	\N	\N
2152	2152	160	1	2026-10-08	purchase	\N	\N
2153	2153	160	1	2026-10-08	purchase	\N	\N
2154	2154	160	1	2026-10-08	purchase	\N	\N
2155	2155	160	1	2026-10-08	donation	\N	\N
2156	2156	160	1	2026-10-08	purchase	\N	\N
2157	2157	160	1	2026-10-08	purchase	\N	\N
2158	2158	160	1	2026-10-08	purchase	\N	\N
2159	2159	160	1	2026-10-08	purchase	\N	\N
2160	2160	160	1	2026-10-08	purchase	\N	\N
2161	2161	160	1	2026-10-08	purchase	\N	\N
2162	2162	160	1	2026-10-08	donation	\N	\N
2163	2163	160	1	2026-10-08	purchase	\N	\N
2164	2164	160	1	2026-10-08	purchase	\N	\N
2165	2165	160	1	2026-10-08	purchase	\N	\N
2166	2166	160	1	2026-10-08	purchase	\N	\N
2167	2167	161	1	2026-10-08	purchase	\N	\N
2168	2168	161	1	2026-10-08	donation	\N	\N
2169	2169	161	1	2026-10-08	purchase	\N	\N
2170	2170	161	1	2026-10-08	purchase	\N	\N
2171	2171	161	1	2026-10-08	purchase	\N	\N
2172	2172	161	1	2026-10-08	purchase	\N	\N
2173	2173	161	1	2026-10-08	purchase	\N	\N
2174	2174	161	1	2026-10-08	purchase	\N	\N
2175	2175	161	1	2026-10-08	donation	\N	\N
2176	2176	161	1	2026-10-08	purchase	\N	\N
2177	2177	161	1	2026-10-08	purchase	\N	\N
2178	2178	161	1	2026-10-08	purchase	\N	\N
2179	2179	161	1	2026-10-08	purchase	\N	\N
2180	2180	161	1	2026-10-08	purchase	\N	\N
2181	2181	161	1	2026-10-08	purchase	\N	\N
2182	2182	161	1	2026-10-08	donation	\N	\N
2183	2183	161	1	2026-10-08	purchase	\N	\N
2184	2184	162	1	2026-10-08	donation	\N	\N
2185	2185	162	1	2026-10-08	purchase	\N	\N
2186	2186	162	1	2026-10-08	purchase	\N	\N
2187	2187	162	1	2026-10-08	purchase	\N	\N
2188	2188	162	1	2026-10-08	purchase	\N	\N
2189	2189	162	1	2026-10-08	purchase	\N	\N
2190	2190	162	1	2026-10-08	purchase	\N	\N
2191	2191	162	1	2026-10-08	donation	\N	\N
2192	2192	162	1	2026-10-08	purchase	\N	\N
2193	2193	162	1	2026-10-08	purchase	\N	\N
2194	2194	162	1	2026-10-08	purchase	\N	\N
2195	2195	162	1	2026-10-08	purchase	\N	\N
2196	2196	162	1	2026-10-08	purchase	\N	\N
2197	2197	162	1	2026-10-08	purchase	\N	\N
2198	2198	162	1	2026-10-08	donation	\N	\N
2199	2199	162	1	2026-10-08	purchase	\N	\N
2200	2200	162	1	2026-10-08	purchase	\N	\N
2201	2201	162	1	2026-10-08	purchase	\N	\N
2202	2202	162	1	2026-10-08	purchase	\N	\N
2203	2203	163	1	2026-10-08	purchase	\N	\N
2204	2204	163	1	2026-10-08	purchase	\N	\N
2205	2205	163	1	2026-10-08	purchase	\N	\N
2206	2206	163	1	2026-10-08	purchase	\N	\N
2207	2207	163	1	2026-10-08	purchase	\N	\N
2208	2208	163	1	2026-10-08	purchase	\N	\N
2209	2209	163	1	2026-10-08	donation	\N	\N
2210	2210	163	1	2026-10-08	purchase	\N	\N
2211	2211	163	1	2026-10-08	purchase	\N	\N
2212	2212	163	1	2026-10-08	purchase	\N	\N
2213	2213	163	1	2026-10-08	purchase	\N	\N
2214	2214	163	1	2026-10-08	purchase	\N	\N
2215	2215	163	1	2026-10-08	purchase	\N	\N
2216	2216	163	1	2026-10-08	donation	\N	\N
2217	2217	163	1	2026-10-08	purchase	\N	\N
2218	2218	163	1	2026-10-08	purchase	\N	\N
2219	2219	163	1	2026-10-08	purchase	\N	\N
2220	2220	164	1	2026-10-08	purchase	\N	\N
2221	2221	164	1	2026-10-08	purchase	\N	\N
2222	2222	164	1	2026-10-08	purchase	\N	\N
2223	2223	164	1	2026-10-08	purchase	\N	\N
2224	2224	164	1	2026-10-08	purchase	\N	\N
2225	2225	164	1	2026-10-08	donation	\N	\N
2226	2226	164	1	2026-10-08	purchase	\N	\N
2227	2227	164	1	2026-10-08	purchase	\N	\N
2228	2228	164	1	2026-10-08	purchase	\N	\N
2229	2229	164	1	2026-10-08	purchase	\N	\N
2230	2230	164	1	2026-10-08	purchase	\N	\N
2231	2231	164	1	2026-10-08	purchase	\N	\N
2232	2232	164	1	2026-10-08	donation	\N	\N
2233	2233	164	1	2026-10-08	purchase	\N	\N
2234	2234	164	1	2026-10-08	purchase	\N	\N
2235	2235	165	1	2026-10-08	purchase	\N	\N
2236	2236	165	1	2026-10-08	purchase	\N	\N
2237	2237	165	1	2026-10-08	purchase	\N	\N
2238	2238	165	1	2026-10-08	purchase	\N	\N
2239	2239	165	1	2026-10-08	donation	\N	\N
2240	2240	165	1	2026-10-08	purchase	\N	\N
2241	2241	165	1	2026-10-08	purchase	\N	\N
2242	2242	165	1	2026-10-08	purchase	\N	\N
2243	2243	165	1	2026-10-08	purchase	\N	\N
2244	2244	165	1	2026-10-08	purchase	\N	\N
2245	2245	165	1	2026-10-08	purchase	\N	\N
2246	2246	165	1	2026-10-08	donation	\N	\N
2247	2247	165	1	2026-10-08	purchase	\N	\N
2248	2248	166	1	2026-10-08	purchase	\N	\N
2249	2249	166	1	2026-10-08	purchase	\N	\N
2250	2250	166	1	2026-10-08	purchase	\N	\N
2251	2251	166	1	2026-10-08	donation	\N	\N
2252	2252	166	1	2026-10-08	purchase	\N	\N
2253	2253	166	1	2026-10-08	purchase	\N	\N
2254	2254	166	1	2026-10-08	purchase	\N	\N
2255	2255	166	1	2026-10-08	purchase	\N	\N
2256	2256	166	1	2026-10-08	purchase	\N	\N
2257	2257	166	1	2026-10-08	purchase	\N	\N
2258	2258	166	1	2026-10-08	donation	\N	\N
2259	2259	166	1	2026-10-08	purchase	\N	\N
2260	2260	166	1	2026-10-08	purchase	\N	\N
2261	2261	166	1	2026-10-08	purchase	\N	\N
2262	2262	166	1	2026-10-08	purchase	\N	\N
2263	2263	167	1	2026-10-08	purchase	\N	\N
2264	2264	167	1	2026-10-08	purchase	\N	\N
2265	2265	167	1	2026-10-08	donation	\N	\N
2266	2266	167	1	2026-10-08	purchase	\N	\N
2267	2267	167	1	2026-10-08	purchase	\N	\N
2268	2268	167	1	2026-10-08	purchase	\N	\N
2269	2269	167	1	2026-10-08	purchase	\N	\N
2270	2270	167	1	2026-10-08	purchase	\N	\N
2271	2271	167	1	2026-10-08	purchase	\N	\N
2272	2272	167	1	2026-10-08	donation	\N	\N
2273	2273	167	1	2026-10-08	purchase	\N	\N
2274	2274	167	1	2026-10-08	purchase	\N	\N
2275	2275	167	1	2026-10-08	purchase	\N	\N
2276	2276	167	1	2026-10-08	purchase	\N	\N
2277	2277	167	1	2026-10-08	purchase	\N	\N
2278	2278	168	1	2026-10-08	purchase	\N	\N
2279	2279	168	1	2026-10-08	donation	\N	\N
2280	2280	168	1	2026-10-08	purchase	\N	\N
2281	2281	168	1	2026-10-08	purchase	\N	\N
2282	2282	168	1	2026-10-08	purchase	\N	\N
2283	2283	168	1	2026-10-08	purchase	\N	\N
2284	2284	168	1	2026-10-08	purchase	\N	\N
2285	2285	168	1	2026-10-08	purchase	\N	\N
2286	2286	168	1	2026-10-08	donation	\N	\N
2287	2287	168	1	2026-10-08	purchase	\N	\N
2288	2288	168	1	2026-10-08	purchase	\N	\N
2289	2289	168	1	2026-10-08	purchase	\N	\N
2290	2290	168	1	2026-10-08	purchase	\N	\N
2291	2291	168	1	2026-10-08	purchase	\N	\N
2292	2292	168	1	2026-10-08	purchase	\N	\N
2293	2293	169	1	2026-10-08	donation	\N	\N
2294	2294	169	1	2026-10-08	purchase	\N	\N
2295	2295	169	1	2026-10-08	purchase	\N	\N
2296	2296	169	1	2026-10-08	purchase	\N	\N
2297	2297	169	1	2026-10-08	purchase	\N	\N
2298	2298	169	1	2026-10-08	purchase	\N	\N
2299	2299	169	1	2026-10-08	purchase	\N	\N
2300	2300	169	1	2026-10-08	donation	\N	\N
2301	2301	169	1	2026-10-08	purchase	\N	\N
2302	2302	169	1	2026-10-08	purchase	\N	\N
2303	2303	169	1	2026-10-08	purchase	\N	\N
2304	2304	169	1	2026-10-08	purchase	\N	\N
2305	2305	169	1	2026-10-08	purchase	\N	\N
2306	2306	170	1	2026-10-08	purchase	\N	\N
2307	2307	170	1	2026-10-08	purchase	\N	\N
2308	2308	170	1	2026-10-08	purchase	\N	\N
2309	2309	170	1	2026-10-08	purchase	\N	\N
2310	2310	170	1	2026-10-08	purchase	\N	\N
2311	2311	170	1	2026-10-08	purchase	\N	\N
2312	2312	170	1	2026-10-08	donation	\N	\N
2313	2313	170	1	2026-10-08	purchase	\N	\N
2314	2314	170	1	2026-10-08	purchase	\N	\N
2315	2315	170	1	2026-10-08	purchase	\N	\N
2316	2316	170	1	2026-10-08	purchase	\N	\N
2317	2317	170	1	2026-10-08	purchase	\N	\N
2318	2318	170	1	2026-10-08	purchase	\N	\N
2319	2319	171	1	2026-10-08	purchase	\N	\N
2320	2320	171	1	2026-10-08	purchase	\N	\N
2321	2321	171	1	2026-10-08	purchase	\N	\N
2322	2322	171	1	2026-10-08	purchase	\N	\N
2323	2323	171	1	2026-10-08	purchase	\N	\N
2324	2324	171	1	2026-10-08	donation	\N	\N
2325	2325	171	1	2026-10-08	purchase	\N	\N
2326	2326	171	1	2026-10-08	purchase	\N	\N
2327	2327	171	1	2026-10-08	purchase	\N	\N
2328	2328	171	1	2026-10-08	purchase	\N	\N
2329	2329	171	1	2026-10-08	purchase	\N	\N
2330	2330	172	1	2026-10-08	purchase	\N	\N
2331	2331	172	1	2026-10-08	purchase	\N	\N
2332	2332	172	1	2026-10-08	purchase	\N	\N
2333	2333	172	1	2026-10-08	purchase	\N	\N
2334	2334	172	1	2026-10-08	donation	\N	\N
2335	2335	172	1	2026-10-08	purchase	\N	\N
2336	2336	172	1	2026-10-08	purchase	\N	\N
2337	2337	172	1	2026-10-08	purchase	\N	\N
2338	2338	172	1	2026-10-08	purchase	\N	\N
2339	2339	172	1	2026-10-08	purchase	\N	\N
2340	2340	172	1	2026-10-08	purchase	\N	\N
2341	2341	173	1	2026-10-08	purchase	\N	\N
2342	2342	173	1	2026-10-08	purchase	\N	\N
2343	2343	173	1	2026-10-08	purchase	\N	\N
2344	2344	173	1	2026-10-08	donation	\N	\N
2345	2345	173	1	2026-10-08	purchase	\N	\N
2346	2346	173	1	2026-10-08	purchase	\N	\N
2347	2347	173	1	2026-10-08	purchase	\N	\N
2348	2348	173	1	2026-10-08	purchase	\N	\N
2349	2349	173	1	2026-10-08	purchase	\N	\N
2350	2350	173	1	2026-10-08	purchase	\N	\N
2351	2351	173	1	2026-10-08	donation	\N	\N
2352	2352	174	1	2026-10-08	purchase	\N	\N
2353	2353	174	1	2026-10-08	purchase	\N	\N
2354	2354	174	1	2026-10-08	donation	\N	\N
2355	2355	174	1	2026-10-08	purchase	\N	\N
2356	2356	174	1	2026-10-08	purchase	\N	\N
2357	2357	174	1	2026-10-08	purchase	\N	\N
2358	2358	174	1	2026-10-08	purchase	\N	\N
2359	2359	174	1	2026-10-08	purchase	\N	\N
2360	2360	174	1	2026-10-08	purchase	\N	\N
2361	2361	174	1	2026-10-08	donation	\N	\N
2362	2362	174	1	2026-10-08	purchase	\N	\N
2363	2363	174	1	2026-10-08	purchase	\N	\N
2364	2364	174	1	2026-10-08	purchase	\N	\N
2365	2365	175	1	2026-10-08	purchase	\N	\N
2366	2366	175	1	2026-10-08	donation	\N	\N
2367	2367	175	1	2026-10-08	purchase	\N	\N
2368	2368	175	1	2026-10-08	purchase	\N	\N
2369	2369	175	1	2026-10-08	purchase	\N	\N
2370	2370	175	1	2026-10-08	purchase	\N	\N
2371	2371	175	1	2026-10-08	purchase	\N	\N
2372	2372	175	1	2026-10-08	purchase	\N	\N
2373	2373	175	1	2026-10-08	donation	\N	\N
2374	2374	175	1	2026-10-08	purchase	\N	\N
2375	2375	175	1	2026-10-08	purchase	\N	\N
2376	2376	176	1	2026-10-08	donation	\N	\N
2377	2377	176	1	2026-10-08	purchase	\N	\N
2378	2378	176	1	2026-10-08	purchase	\N	\N
2379	2379	176	1	2026-10-08	purchase	\N	\N
2380	2380	176	1	2026-10-08	purchase	\N	\N
2381	2381	176	1	2026-10-08	purchase	\N	\N
2382	2382	176	1	2026-10-08	purchase	\N	\N
2383	2383	176	1	2026-10-08	donation	\N	\N
2384	2384	176	1	2026-10-08	purchase	\N	\N
2385	2385	176	1	2026-10-08	purchase	\N	\N
2386	2386	176	1	2026-10-08	purchase	\N	\N
2387	2387	176	1	2026-10-08	purchase	\N	\N
2388	2388	176	1	2026-10-08	purchase	\N	\N
2389	2389	177	1	2026-10-08	purchase	\N	\N
2390	2390	177	1	2026-10-08	purchase	\N	\N
2391	2391	177	1	2026-10-08	purchase	\N	\N
2392	2392	177	1	2026-10-08	purchase	\N	\N
2393	2393	177	1	2026-10-08	purchase	\N	\N
2394	2394	177	1	2026-10-08	purchase	\N	\N
2395	2395	177	1	2026-10-08	donation	\N	\N
2396	2396	177	1	2026-10-08	purchase	\N	\N
2397	2397	177	1	2026-10-08	purchase	\N	\N
2398	2398	177	1	2026-10-08	purchase	\N	\N
2399	2399	177	1	2026-10-08	purchase	\N	\N
2400	2400	177	1	2026-10-08	purchase	\N	\N
2401	2401	177	1	2026-10-08	purchase	\N	\N
2402	2402	178	1	2026-10-08	purchase	\N	\N
2403	2403	178	1	2026-10-08	purchase	\N	\N
2404	2404	178	1	2026-10-08	purchase	\N	\N
2405	2405	178	1	2026-10-08	purchase	\N	\N
2406	2406	178	1	2026-10-08	purchase	\N	\N
2407	2407	178	1	2026-10-08	donation	\N	\N
2408	2408	178	1	2026-10-08	purchase	\N	\N
2409	2409	178	1	2026-10-08	purchase	\N	\N
2410	2410	178	1	2026-10-08	purchase	\N	\N
2411	2411	178	1	2026-10-08	purchase	\N	\N
2412	2412	178	1	2026-10-08	purchase	\N	\N
2413	2413	178	1	2026-10-08	purchase	\N	\N
2414	2414	178	1	2026-10-08	donation	\N	\N
2415	2415	178	1	2026-10-08	purchase	\N	\N
2416	2416	178	1	2026-10-08	purchase	\N	\N
2417	2417	178	1	2026-10-08	purchase	\N	\N
2418	2418	178	1	2026-10-08	purchase	\N	\N
2419	2419	179	1	2026-10-08	purchase	\N	\N
2420	2420	179	1	2026-10-08	purchase	\N	\N
2421	2421	179	1	2026-10-08	purchase	\N	\N
2422	2422	179	1	2026-10-08	purchase	\N	\N
2423	2423	179	1	2026-10-08	donation	\N	\N
2424	2424	179	1	2026-10-08	purchase	\N	\N
2425	2425	179	1	2026-10-08	purchase	\N	\N
2426	2426	179	1	2026-10-08	purchase	\N	\N
2427	2427	179	1	2026-10-08	purchase	\N	\N
2428	2428	179	1	2026-10-08	purchase	\N	\N
2429	2429	179	1	2026-10-08	purchase	\N	\N
2430	2430	179	1	2026-10-08	donation	\N	\N
2431	2431	179	1	2026-10-08	purchase	\N	\N
2432	2432	179	1	2026-10-08	purchase	\N	\N
2433	2433	179	1	2026-10-08	purchase	\N	\N
2434	2434	180	1	2026-10-08	purchase	\N	\N
2435	2435	180	1	2026-10-08	purchase	\N	\N
2436	2436	180	1	2026-10-08	purchase	\N	\N
2437	2437	180	1	2026-10-08	donation	\N	\N
2438	2438	180	1	2026-10-08	purchase	\N	\N
2439	2439	180	1	2026-10-08	purchase	\N	\N
2440	2440	180	1	2026-10-08	purchase	\N	\N
2441	2441	180	1	2026-10-08	purchase	\N	\N
2442	2442	180	1	2026-10-08	purchase	\N	\N
2443	2443	180	1	2026-10-08	purchase	\N	\N
2444	2444	180	1	2026-10-08	donation	\N	\N
2445	2445	180	1	2026-10-08	purchase	\N	\N
2446	2446	180	1	2026-10-08	purchase	\N	\N
2447	2447	180	1	2026-10-08	purchase	\N	\N
2448	2448	180	1	2026-10-08	purchase	\N	\N
2449	2449	180	1	2026-10-08	purchase	\N	\N
2450	2450	180	1	2026-10-08	purchase	\N	\N
2451	2451	181	1	2026-10-08	purchase	\N	\N
2452	2452	181	1	2026-10-08	purchase	\N	\N
2453	2453	181	1	2026-10-08	donation	\N	\N
2454	2454	181	1	2026-10-08	purchase	\N	\N
2455	2455	181	1	2026-10-08	purchase	\N	\N
2456	2456	181	1	2026-10-08	purchase	\N	\N
2457	2457	181	1	2026-10-08	purchase	\N	\N
2458	2458	181	1	2026-10-08	purchase	\N	\N
2459	2459	181	1	2026-10-08	purchase	\N	\N
2460	2460	181	1	2026-10-08	donation	\N	\N
2461	2461	181	1	2026-10-08	purchase	\N	\N
2462	2462	182	1	2026-10-08	purchase	\N	\N
2463	2463	182	1	2026-10-08	donation	\N	\N
2464	2464	182	1	2026-10-08	purchase	\N	\N
2465	2465	182	1	2026-10-08	purchase	\N	\N
2466	2466	182	1	2026-10-08	purchase	\N	\N
2467	2467	182	1	2026-10-08	purchase	\N	\N
2468	2468	182	1	2026-10-08	purchase	\N	\N
2469	2469	182	1	2026-10-08	purchase	\N	\N
2470	2470	182	1	2026-10-08	donation	\N	\N
2471	2471	183	1	2026-10-08	donation	\N	\N
2472	2472	183	1	2026-10-08	purchase	\N	\N
2473	2473	183	1	2026-10-08	purchase	\N	\N
2474	2474	183	1	2026-10-08	purchase	\N	\N
2475	2475	183	1	2026-10-08	purchase	\N	\N
2476	2476	183	1	2026-10-08	purchase	\N	\N
2477	2477	183	1	2026-10-08	purchase	\N	\N
2478	2478	183	1	2026-10-08	donation	\N	\N
2479	2479	183	1	2026-10-08	purchase	\N	\N
2480	2480	184	1	2026-10-08	purchase	\N	\N
2481	2481	184	1	2026-10-08	purchase	\N	\N
2482	2482	184	1	2026-10-08	purchase	\N	\N
2483	2483	184	1	2026-10-08	purchase	\N	\N
2484	2484	184	1	2026-10-08	purchase	\N	\N
2485	2485	184	1	2026-10-08	purchase	\N	\N
2486	2486	184	1	2026-10-08	donation	\N	\N
2487	2487	184	1	2026-10-08	purchase	\N	\N
2488	2488	185	1	2026-10-08	purchase	\N	\N
2489	2489	185	1	2026-10-08	purchase	\N	\N
2490	2490	185	1	2026-10-08	purchase	\N	\N
2491	2491	185	1	2026-10-08	purchase	\N	\N
2492	2492	185	1	2026-10-08	purchase	\N	\N
2493	2493	185	1	2026-10-08	donation	\N	\N
2494	2494	185	1	2026-10-08	purchase	\N	\N
2495	2495	185	1	2026-10-08	purchase	\N	\N
2496	2496	185	1	2026-10-08	purchase	\N	\N
2497	2497	186	1	2026-10-08	purchase	\N	\N
2498	2498	186	1	2026-10-08	purchase	\N	\N
2499	2499	186	1	2026-10-08	purchase	\N	\N
2500	2500	186	1	2026-10-08	purchase	\N	\N
2501	2501	186	1	2026-10-08	donation	\N	\N
2502	2502	186	1	2026-10-08	purchase	\N	\N
2503	2503	186	1	2026-10-08	purchase	\N	\N
2504	2504	186	1	2026-10-08	purchase	\N	\N
2505	2505	187	1	2026-10-08	purchase	\N	\N
2506	2506	187	1	2026-10-08	purchase	\N	\N
2507	2507	187	1	2026-10-08	purchase	\N	\N
2508	2508	187	1	2026-10-08	donation	\N	\N
2509	2509	187	1	2026-10-08	purchase	\N	\N
2510	2510	187	1	2026-10-08	purchase	\N	\N
2511	2511	187	1	2026-10-08	purchase	\N	\N
2512	2512	188	1	2026-10-08	purchase	\N	\N
2513	2513	188	1	2026-10-08	purchase	\N	\N
2514	2514	188	1	2026-10-08	donation	\N	\N
2515	2515	188	1	2026-10-08	purchase	\N	\N
2516	2516	188	1	2026-10-08	purchase	\N	\N
2517	2517	188	1	2026-10-08	purchase	\N	\N
2518	2518	188	1	2026-10-08	purchase	\N	\N
2519	2519	188	1	2026-10-08	purchase	\N	\N
2520	2520	189	1	2026-10-08	purchase	\N	\N
2521	2521	189	1	2026-10-08	donation	\N	\N
2522	2522	189	1	2026-10-08	purchase	\N	\N
2523	2523	189	1	2026-10-08	purchase	\N	\N
2524	2524	189	1	2026-10-08	purchase	\N	\N
2525	2525	189	1	2026-10-08	purchase	\N	\N
2526	2526	189	1	2026-10-08	purchase	\N	\N
2527	2527	189	1	2026-10-08	purchase	\N	\N
2528	2528	190	1	2026-10-08	donation	\N	\N
2529	2529	190	1	2026-10-08	purchase	\N	\N
2530	2530	190	1	2026-10-08	purchase	\N	\N
2531	2531	190	1	2026-10-08	purchase	\N	\N
2532	2532	190	1	2026-10-08	purchase	\N	\N
2533	2533	190	1	2026-10-08	purchase	\N	\N
2534	2534	190	1	2026-10-08	purchase	\N	\N
2535	2535	191	1	2026-10-08	purchase	\N	\N
2536	2536	191	1	2026-10-08	purchase	\N	\N
2537	2537	191	1	2026-10-08	purchase	\N	\N
2538	2538	191	1	2026-10-08	purchase	\N	\N
2539	2539	191	1	2026-10-08	purchase	\N	\N
2540	2540	191	1	2026-10-08	purchase	\N	\N
2541	2541	191	1	2026-10-08	donation	\N	\N
2542	2542	191	1	2026-10-08	purchase	\N	\N
2543	2543	191	1	2026-10-08	purchase	\N	\N
2544	2544	191	1	2026-10-08	purchase	\N	\N
2545	2545	191	1	2026-10-08	purchase	\N	\N
2546	2546	191	1	2026-10-08	purchase	\N	\N
2547	2547	191	1	2026-10-08	purchase	\N	\N
2548	2548	192	1	2026-10-08	purchase	\N	\N
2549	2549	192	1	2026-10-08	purchase	\N	\N
2550	2550	192	1	2026-10-08	purchase	\N	\N
2551	2551	192	1	2026-10-08	purchase	\N	\N
2552	2552	192	1	2026-10-08	purchase	\N	\N
2553	2553	192	1	2026-10-08	donation	\N	\N
2554	2554	192	1	2026-10-08	purchase	\N	\N
2555	2555	192	1	2026-10-08	purchase	\N	\N
2556	2556	192	1	2026-10-08	purchase	\N	\N
2557	2557	192	1	2026-10-08	purchase	\N	\N
2558	2558	192	1	2026-10-08	purchase	\N	\N
2559	2559	193	1	2026-10-08	purchase	\N	\N
2560	2560	193	1	2026-10-08	purchase	\N	\N
2561	2561	193	1	2026-10-08	purchase	\N	\N
2562	2562	193	1	2026-10-08	purchase	\N	\N
2563	2563	193	1	2026-10-08	donation	\N	\N
2564	2564	193	1	2026-10-08	purchase	\N	\N
2565	2565	193	1	2026-10-08	purchase	\N	\N
2566	2566	193	1	2026-10-08	purchase	\N	\N
2567	2567	193	1	2026-10-08	purchase	\N	\N
2568	2568	193	1	2026-10-08	purchase	\N	\N
2569	2569	193	1	2026-10-08	purchase	\N	\N
2570	2570	193	1	2026-10-08	donation	\N	\N
2571	2571	193	1	2026-10-08	purchase	\N	\N
2572	2572	193	1	2026-10-08	purchase	\N	\N
2573	2573	193	1	2026-10-08	purchase	\N	\N
2574	2574	193	1	2026-10-08	purchase	\N	\N
2575	2575	193	1	2026-10-08	purchase	\N	\N
2576	2576	193	1	2026-10-08	purchase	\N	\N
2577	2577	193	1	2026-10-08	donation	\N	\N
2578	2578	194	1	2026-10-08	purchase	\N	\N
2579	2579	194	1	2026-10-08	purchase	\N	\N
2580	2580	194	1	2026-10-08	purchase	\N	\N
2581	2581	194	1	2026-10-08	donation	\N	\N
2582	2582	194	1	2026-10-08	purchase	\N	\N
2583	2583	194	1	2026-10-08	purchase	\N	\N
2584	2584	194	1	2026-10-08	purchase	\N	\N
2585	2585	194	1	2026-10-08	purchase	\N	\N
2586	2586	194	1	2026-10-08	purchase	\N	\N
2587	2587	194	1	2026-10-08	purchase	\N	\N
2588	2588	194	1	2026-10-08	donation	\N	\N
2589	2589	194	1	2026-10-08	purchase	\N	\N
2590	2590	194	1	2026-10-08	purchase	\N	\N
2591	2591	194	1	2026-10-08	purchase	\N	\N
2592	2592	194	1	2026-10-08	purchase	\N	\N
2593	2593	195	1	2026-10-08	purchase	\N	\N
2594	2594	195	1	2026-10-08	purchase	\N	\N
2595	2595	195	1	2026-10-08	donation	\N	\N
2596	2596	195	1	2026-10-08	purchase	\N	\N
2597	2597	195	1	2026-10-08	purchase	\N	\N
2598	2598	195	1	2026-10-08	purchase	\N	\N
2599	2599	195	1	2026-10-08	purchase	\N	\N
2600	2600	195	1	2026-10-08	purchase	\N	\N
2601	2601	195	1	2026-10-08	purchase	\N	\N
2602	2602	196	1	2026-10-08	purchase	\N	\N
2603	2603	196	1	2026-10-08	donation	\N	\N
2604	2604	196	1	2026-10-08	purchase	\N	\N
2605	2605	196	1	2026-10-08	purchase	\N	\N
2606	2606	196	1	2026-10-08	purchase	\N	\N
2607	2607	196	1	2026-10-08	purchase	\N	\N
2608	2608	196	1	2026-10-08	purchase	\N	\N
2609	2609	196	1	2026-10-08	purchase	\N	\N
2610	2610	196	1	2026-10-08	donation	\N	\N
2611	2611	196	1	2026-10-08	purchase	\N	\N
2612	2612	196	1	2026-10-08	purchase	\N	\N
2613	2613	196	1	2026-10-08	purchase	\N	\N
2614	2614	196	1	2026-10-08	purchase	\N	\N
2615	2615	197	1	2026-10-08	donation	\N	\N
2616	2616	197	1	2026-10-08	purchase	\N	\N
2617	2617	197	1	2026-10-08	purchase	\N	\N
2618	2618	197	1	2026-10-08	purchase	\N	\N
2619	2619	197	1	2026-10-08	purchase	\N	\N
2620	2620	197	1	2026-10-08	purchase	\N	\N
2621	2621	197	1	2026-10-08	purchase	\N	\N
2622	2622	197	1	2026-10-08	donation	\N	\N
2623	2623	197	1	2026-10-08	purchase	\N	\N
2624	2624	197	1	2026-10-08	purchase	\N	\N
2625	2625	197	1	2026-10-08	purchase	\N	\N
2626	2626	198	1	2026-10-08	purchase	\N	\N
2627	2627	199	1	2026-10-08	purchase	\N	\N
2628	2628	199	1	2026-10-08	purchase	\N	\N
2629	2629	199	1	2026-10-08	purchase	\N	\N
2630	2630	199	1	2026-10-08	purchase	\N	\N
2631	2631	199	1	2026-10-08	purchase	\N	\N
2632	2632	199	1	2026-10-08	donation	\N	\N
2633	2633	199	1	2026-10-08	purchase	\N	\N
2634	2634	199	1	2026-10-08	purchase	\N	\N
2635	2635	199	1	2026-10-08	purchase	\N	\N
2636	2636	199	1	2026-10-08	purchase	\N	\N
2637	2637	199	1	2026-10-08	purchase	\N	\N
2638	2638	199	1	2026-10-08	purchase	\N	\N
2639	2639	199	1	2026-10-08	donation	\N	\N
2640	2640	199	1	2026-10-08	purchase	\N	\N
2641	2641	199	1	2026-10-08	purchase	\N	\N
2642	2642	199	1	2026-10-08	purchase	\N	\N
2643	2643	199	1	2026-10-08	purchase	\N	\N
2644	2644	199	1	2026-10-08	purchase	\N	\N
2645	2645	199	1	2026-10-08	purchase	\N	\N
2646	2646	199	1	2026-10-08	donation	\N	\N
2647	2647	199	1	2026-10-08	purchase	\N	\N
2648	2648	200	1	2026-10-08	purchase	\N	\N
2649	2649	200	1	2026-10-08	purchase	\N	\N
2650	2650	200	1	2026-10-08	purchase	\N	\N
2651	2651	200	1	2026-10-08	purchase	\N	\N
2652	2652	200	1	2026-10-08	donation	\N	\N
2653	2653	200	1	2026-10-08	purchase	\N	\N
2654	2654	200	1	2026-10-08	purchase	\N	\N
2655	2655	200	1	2026-10-08	purchase	\N	\N
2656	2656	200	1	2026-10-08	purchase	\N	\N
2657	2657	200	1	2026-10-08	purchase	\N	\N
2658	2658	200	1	2026-10-08	purchase	\N	\N
2659	2659	200	1	2026-10-08	donation	\N	\N
2660	2660	200	1	2026-10-08	purchase	\N	\N
2661	2661	200	1	2026-10-08	purchase	\N	\N
2662	2662	200	1	2026-10-08	purchase	\N	\N
2663	2663	200	1	2026-10-08	purchase	\N	\N
2664	2664	200	1	2026-10-08	purchase	\N	\N
2665	2665	201	1	2026-10-08	purchase	\N	\N
2666	2666	201	1	2026-10-08	purchase	\N	\N
2667	2667	201	1	2026-10-08	purchase	\N	\N
2668	2668	201	1	2026-10-08	donation	\N	\N
2669	2669	201	1	2026-10-08	purchase	\N	\N
2670	2670	201	1	2026-10-08	purchase	\N	\N
2671	2671	201	1	2026-10-08	purchase	\N	\N
2672	2672	201	1	2026-10-08	purchase	\N	\N
2673	2673	201	1	2026-10-08	purchase	\N	\N
2674	2674	201	1	2026-10-08	purchase	\N	\N
2675	2675	201	1	2026-10-08	donation	\N	\N
2676	2676	201	1	2026-10-08	purchase	\N	\N
2677	2677	201	1	2026-10-08	purchase	\N	\N
2678	2678	201	1	2026-10-08	purchase	\N	\N
2679	2679	201	1	2026-10-08	purchase	\N	\N
2680	2680	201	1	2026-10-08	purchase	\N	\N
2681	2681	201	1	2026-10-08	purchase	\N	\N
2682	2682	202	1	2026-10-08	purchase	\N	\N
2683	2683	202	1	2026-10-08	purchase	\N	\N
2684	2684	202	1	2026-10-08	donation	\N	\N
2685	2685	202	1	2026-10-08	purchase	\N	\N
2686	2686	202	1	2026-10-08	purchase	\N	\N
2687	2687	202	1	2026-10-08	purchase	\N	\N
2688	2688	202	1	2026-10-08	purchase	\N	\N
2689	2689	202	1	2026-10-08	purchase	\N	\N
2690	2690	202	1	2026-10-08	purchase	\N	\N
2691	2691	202	1	2026-10-08	donation	\N	\N
2692	2692	202	1	2026-10-08	purchase	\N	\N
2693	2693	202	1	2026-10-08	purchase	\N	\N
2694	2694	202	1	2026-10-08	purchase	\N	\N
2695	2695	202	1	2026-10-08	purchase	\N	\N
2696	2696	202	1	2026-10-08	purchase	\N	\N
2697	2697	203	1	2026-10-08	purchase	\N	\N
2698	2698	203	1	2026-10-08	donation	\N	\N
2699	2699	203	1	2026-10-08	purchase	\N	\N
2700	2700	203	1	2026-10-08	purchase	\N	\N
2701	2701	203	1	2026-10-08	purchase	\N	\N
2702	2702	203	1	2026-10-08	purchase	\N	\N
2703	2703	203	1	2026-10-08	purchase	\N	\N
2704	2704	203	1	2026-10-08	purchase	\N	\N
2705	2705	203	1	2026-10-08	donation	\N	\N
2706	2706	203	1	2026-10-08	purchase	\N	\N
2707	2707	203	1	2026-10-08	purchase	\N	\N
2708	2708	203	1	2026-10-08	purchase	\N	\N
2709	2709	203	1	2026-10-08	purchase	\N	\N
2710	2710	203	1	2026-10-08	purchase	\N	\N
2711	2711	203	1	2026-10-08	purchase	\N	\N
2712	2712	203	1	2026-10-08	donation	\N	\N
2713	2713	203	1	2026-10-08	purchase	\N	\N
2714	2714	203	1	2026-10-08	purchase	\N	\N
2715	2715	203	1	2026-10-08	purchase	\N	\N
2716	2716	204	1	2026-10-08	donation	\N	\N
2717	2717	204	1	2026-10-08	purchase	\N	\N
2718	2718	204	1	2026-10-08	purchase	\N	\N
2719	2719	204	1	2026-10-08	purchase	\N	\N
2720	2720	204	1	2026-10-08	purchase	\N	\N
2721	2721	204	1	2026-10-08	purchase	\N	\N
2722	2722	204	1	2026-10-08	purchase	\N	\N
2723	2723	204	1	2026-10-08	donation	\N	\N
2724	2724	204	1	2026-10-08	purchase	\N	\N
2725	2725	204	1	2026-10-08	purchase	\N	\N
2726	2726	204	1	2026-10-08	purchase	\N	\N
2727	2727	204	1	2026-10-08	purchase	\N	\N
2728	2728	204	1	2026-10-08	purchase	\N	\N
2729	2729	205	1	2026-10-08	purchase	\N	\N
2730	2730	205	1	2026-10-08	purchase	\N	\N
2731	2731	205	1	2026-10-08	purchase	\N	\N
2732	2732	205	1	2026-10-08	purchase	\N	\N
2733	2733	205	1	2026-10-08	purchase	\N	\N
2734	2734	205	1	2026-10-08	purchase	\N	\N
2735	2735	205	1	2026-10-08	donation	\N	\N
2736	2736	205	1	2026-10-08	purchase	\N	\N
2737	2737	205	1	2026-10-08	purchase	\N	\N
2738	2738	205	1	2026-10-08	purchase	\N	\N
2739	2739	205	1	2026-10-08	purchase	\N	\N
2740	2740	205	1	2026-10-08	purchase	\N	\N
2741	2741	205	1	2026-10-08	purchase	\N	\N
2742	2742	205	1	2026-10-08	donation	\N	\N
2743	2743	205	1	2026-10-08	purchase	\N	\N
2744	2744	205	1	2026-10-08	purchase	\N	\N
2745	2745	205	1	2026-10-08	purchase	\N	\N
2746	2746	206	1	2026-10-08	purchase	\N	\N
2747	2747	206	1	2026-10-08	purchase	\N	\N
2748	2748	206	1	2026-10-08	purchase	\N	\N
2749	2749	206	1	2026-10-08	purchase	\N	\N
2750	2750	206	1	2026-10-08	purchase	\N	\N
2751	2751	206	1	2026-10-08	donation	\N	\N
2752	2752	206	1	2026-10-08	purchase	\N	\N
2753	2753	206	1	2026-10-08	purchase	\N	\N
2754	2754	206	1	2026-10-08	purchase	\N	\N
2755	2755	206	1	2026-10-08	purchase	\N	\N
2756	2756	206	1	2026-10-08	purchase	\N	\N
2757	2757	206	1	2026-10-08	purchase	\N	\N
2758	2758	206	1	2026-10-08	donation	\N	\N
2759	2759	206	1	2026-10-08	purchase	\N	\N
2760	2760	206	1	2026-10-08	purchase	\N	\N
2761	2761	207	1	2026-10-08	purchase	\N	\N
2762	2762	207	1	2026-10-08	purchase	\N	\N
2763	2763	207	1	2026-10-08	purchase	\N	\N
2764	2764	207	1	2026-10-08	purchase	\N	\N
2765	2765	207	1	2026-10-08	donation	\N	\N
2766	2766	207	1	2026-10-08	purchase	\N	\N
2767	2767	207	1	2026-10-08	purchase	\N	\N
2768	2768	207	1	2026-10-08	purchase	\N	\N
2769	2769	207	1	2026-10-08	purchase	\N	\N
2770	2770	207	1	2026-10-08	purchase	\N	\N
2771	2771	207	1	2026-10-08	purchase	\N	\N
2772	2772	207	1	2026-10-08	donation	\N	\N
2773	2773	207	1	2026-10-08	purchase	\N	\N
2774	2774	207	1	2026-10-08	purchase	\N	\N
2775	2775	207	1	2026-10-08	purchase	\N	\N
2776	2776	207	1	2026-10-08	purchase	\N	\N
2777	2777	207	1	2026-10-08	purchase	\N	\N
2778	2778	207	1	2026-10-08	purchase	\N	\N
2779	2779	207	1	2026-10-08	donation	\N	\N
2780	2780	208	1	2026-10-08	purchase	\N	\N
2781	2781	208	1	2026-10-08	purchase	\N	\N
2782	2782	208	1	2026-10-08	purchase	\N	\N
2783	2783	208	1	2026-10-08	donation	\N	\N
2784	2784	208	1	2026-10-08	purchase	\N	\N
2785	2785	208	1	2026-10-08	purchase	\N	\N
2786	2786	208	1	2026-10-08	purchase	\N	\N
2787	2787	208	1	2026-10-08	purchase	\N	\N
2788	2788	208	1	2026-10-08	purchase	\N	\N
2789	2789	208	1	2026-10-08	purchase	\N	\N
2790	2790	208	1	2026-10-08	donation	\N	\N
2791	2791	208	1	2026-10-08	purchase	\N	\N
2792	2792	208	1	2026-10-08	purchase	\N	\N
2793	2793	208	1	2026-10-08	purchase	\N	\N
2794	2794	208	1	2026-10-08	purchase	\N	\N
2795	2795	209	1	2026-10-08	purchase	\N	\N
2796	2796	209	1	2026-10-08	purchase	\N	\N
2797	2797	209	1	2026-10-08	donation	\N	\N
2798	2798	209	1	2026-10-08	purchase	\N	\N
2799	2799	209	1	2026-10-08	purchase	\N	\N
2800	2800	209	1	2026-10-08	purchase	\N	\N
2801	2801	209	1	2026-10-08	purchase	\N	\N
2802	2802	209	1	2026-10-08	purchase	\N	\N
2803	2803	209	1	2026-10-08	purchase	\N	\N
2804	2804	209	1	2026-10-08	donation	\N	\N
2805	2805	209	1	2026-10-08	purchase	\N	\N
2806	2806	209	1	2026-10-08	purchase	\N	\N
2807	2807	209	1	2026-10-08	purchase	\N	\N
2808	2808	209	1	2026-10-08	purchase	\N	\N
2809	2809	209	1	2026-10-08	purchase	\N	\N
2810	2810	209	1	2026-10-08	purchase	\N	\N
2811	2811	209	1	2026-10-08	donation	\N	\N
2812	2812	210	1	2026-10-08	purchase	\N	\N
2813	2813	210	1	2026-10-08	donation	\N	\N
2814	2814	210	1	2026-10-08	purchase	\N	\N
2815	2815	210	1	2026-10-08	purchase	\N	\N
2816	2816	210	1	2026-10-08	purchase	\N	\N
2817	2817	210	1	2026-10-08	purchase	\N	\N
2818	2818	210	1	2026-10-08	purchase	\N	\N
2819	2819	210	1	2026-10-08	purchase	\N	\N
2820	2820	210	1	2026-10-08	donation	\N	\N
2821	2821	210	1	2026-10-08	purchase	\N	\N
2822	2822	210	1	2026-10-08	purchase	\N	\N
2823	2823	210	1	2026-10-08	purchase	\N	\N
2824	2824	210	1	2026-10-08	purchase	\N	\N
2825	2825	210	1	2026-10-08	purchase	\N	\N
2826	2826	210	1	2026-10-08	purchase	\N	\N
2827	2827	211	1	2026-10-08	donation	\N	\N
2828	2828	211	1	2026-10-08	purchase	\N	\N
2829	2829	211	1	2026-10-08	purchase	\N	\N
2830	2830	211	1	2026-10-08	purchase	\N	\N
2831	2831	211	1	2026-10-08	purchase	\N	\N
2832	2832	211	1	2026-10-08	purchase	\N	\N
2833	2833	211	1	2026-10-08	purchase	\N	\N
2834	2834	211	1	2026-10-08	donation	\N	\N
2835	2835	211	1	2026-10-08	purchase	\N	\N
2836	2836	211	1	2026-10-08	purchase	\N	\N
2837	2837	211	1	2026-10-08	purchase	\N	\N
2838	2838	211	1	2026-10-08	purchase	\N	\N
2839	2839	211	1	2026-10-08	purchase	\N	\N
2840	2840	211	1	2026-10-08	purchase	\N	\N
2841	2841	211	1	2026-10-08	donation	\N	\N
2842	2842	212	1	2026-10-08	purchase	\N	\N
2843	2843	212	1	2026-10-08	purchase	\N	\N
2844	2844	212	1	2026-10-08	purchase	\N	\N
2845	2845	212	1	2026-10-08	purchase	\N	\N
2846	2846	212	1	2026-10-08	purchase	\N	\N
2847	2847	212	1	2026-10-08	purchase	\N	\N
2848	2848	212	1	2026-10-08	donation	\N	\N
2849	2849	212	1	2026-10-08	purchase	\N	\N
2850	2850	212	1	2026-10-08	purchase	\N	\N
2851	2851	212	1	2026-10-08	purchase	\N	\N
2852	2852	212	1	2026-10-08	purchase	\N	\N
2853	2853	212	1	2026-10-08	purchase	\N	\N
2854	2854	212	1	2026-10-08	purchase	\N	\N
2855	2855	213	1	2026-10-08	purchase	\N	\N
2856	2856	213	1	2026-10-08	purchase	\N	\N
2857	2857	213	1	2026-10-08	purchase	\N	\N
2858	2858	213	1	2026-10-08	purchase	\N	\N
2859	2859	213	1	2026-10-08	purchase	\N	\N
2860	2860	213	1	2026-10-08	donation	\N	\N
2861	2861	213	1	2026-10-08	purchase	\N	\N
2862	2862	213	1	2026-10-08	purchase	\N	\N
2863	2863	213	1	2026-10-08	purchase	\N	\N
2864	2864	213	1	2026-10-08	purchase	\N	\N
2865	2865	213	1	2026-10-08	purchase	\N	\N
2866	2866	213	1	2026-10-08	purchase	\N	\N
2867	2867	213	1	2026-10-08	donation	\N	\N
2868	2868	214	1	2026-10-08	purchase	\N	\N
2869	2869	214	1	2026-10-08	purchase	\N	\N
2870	2870	214	1	2026-10-08	purchase	\N	\N
2871	2871	214	1	2026-10-08	purchase	\N	\N
2872	2872	214	1	2026-10-08	donation	\N	\N
2873	2873	214	1	2026-10-08	purchase	\N	\N
2874	2874	214	1	2026-10-08	purchase	\N	\N
2875	2875	214	1	2026-10-08	purchase	\N	\N
2876	2876	214	1	2026-10-08	purchase	\N	\N
2877	2877	214	1	2026-10-08	purchase	\N	\N
2878	2878	214	1	2026-10-08	purchase	\N	\N
2879	2879	214	1	2026-10-08	donation	\N	\N
2880	2880	214	1	2026-10-08	purchase	\N	\N
2881	2881	215	1	2026-10-08	purchase	\N	\N
2882	2882	215	1	2026-10-08	purchase	\N	\N
2883	2883	215	1	2026-10-08	purchase	\N	\N
2884	2884	215	1	2026-10-08	donation	\N	\N
2885	2885	215	1	2026-10-08	purchase	\N	\N
2886	2886	215	1	2026-10-08	purchase	\N	\N
2887	2887	215	1	2026-10-08	purchase	\N	\N
2888	2888	215	1	2026-10-08	purchase	\N	\N
2889	2889	215	1	2026-10-08	purchase	\N	\N
2890	2890	215	1	2026-10-08	purchase	\N	\N
2891	2891	215	1	2026-10-08	donation	\N	\N
2892	2892	215	1	2026-10-08	purchase	\N	\N
2893	2893	215	1	2026-10-08	purchase	\N	\N
2894	2894	216	1	2026-10-08	purchase	\N	\N
2895	2895	216	1	2026-10-08	purchase	\N	\N
2896	2896	216	1	2026-10-08	donation	\N	\N
2897	2897	216	1	2026-10-08	purchase	\N	\N
2898	2898	216	1	2026-10-08	purchase	\N	\N
2899	2899	216	1	2026-10-08	purchase	\N	\N
2900	2900	216	1	2026-10-08	purchase	\N	\N
2901	2901	216	1	2026-10-08	purchase	\N	\N
2902	2902	216	1	2026-10-08	purchase	\N	\N
2903	2903	216	1	2026-10-08	donation	\N	\N
2904	2904	216	1	2026-10-08	purchase	\N	\N
2905	2905	217	1	2026-10-08	purchase	\N	\N
2906	2906	217	1	2026-10-08	donation	\N	\N
2907	2907	217	1	2026-10-08	purchase	\N	\N
2908	2908	217	1	2026-10-08	purchase	\N	\N
2909	2909	217	1	2026-10-08	purchase	\N	\N
2910	2910	217	1	2026-10-08	purchase	\N	\N
2911	2911	217	1	2026-10-08	purchase	\N	\N
2912	2912	217	1	2026-10-08	purchase	\N	\N
2913	2913	217	1	2026-10-08	donation	\N	\N
2914	2914	218	1	2026-10-08	donation	\N	\N
2915	2915	218	1	2026-10-08	purchase	\N	\N
2916	2916	218	1	2026-10-08	purchase	\N	\N
2917	2917	218	1	2026-10-08	purchase	\N	\N
2918	2918	218	1	2026-10-08	purchase	\N	\N
2919	2919	218	1	2026-10-08	purchase	\N	\N
2920	2920	218	1	2026-10-08	purchase	\N	\N
2921	2921	218	1	2026-10-08	donation	\N	\N
2922	2922	218	1	2026-10-08	purchase	\N	\N
2923	2923	218	1	2026-10-08	purchase	\N	\N
2924	2924	218	1	2026-10-08	purchase	\N	\N
2925	2925	218	1	2026-10-08	purchase	\N	\N
2926	2926	218	1	2026-10-08	purchase	\N	\N
2927	2927	219	1	2026-10-08	purchase	\N	\N
2928	2928	219	1	2026-10-08	purchase	\N	\N
2929	2929	219	1	2026-10-08	purchase	\N	\N
2930	2930	219	1	2026-10-08	purchase	\N	\N
2931	2931	219	1	2026-10-08	purchase	\N	\N
2932	2932	219	1	2026-10-08	purchase	\N	\N
2933	2933	219	1	2026-10-08	donation	\N	\N
2934	2934	219	1	2026-10-08	purchase	\N	\N
2935	2935	219	1	2026-10-08	purchase	\N	\N
2936	2936	219	1	2026-10-08	purchase	\N	\N
2937	2937	219	1	2026-10-08	purchase	\N	\N
2938	2938	220	1	2026-10-08	purchase	\N	\N
2939	2939	220	1	2026-10-08	purchase	\N	\N
2940	2940	220	1	2026-10-08	purchase	\N	\N
2941	2941	220	1	2026-10-08	purchase	\N	\N
2942	2942	220	1	2026-10-08	purchase	\N	\N
2943	2943	220	1	2026-10-08	donation	\N	\N
2944	2944	220	1	2026-10-08	purchase	\N	\N
2945	2945	220	1	2026-10-08	purchase	\N	\N
2946	2946	221	1	2026-10-08	purchase	\N	\N
2947	2947	221	1	2026-10-08	purchase	\N	\N
2948	2948	221	1	2026-10-08	purchase	\N	\N
2949	2949	221	1	2026-10-08	purchase	\N	\N
2950	2950	221	1	2026-10-08	donation	\N	\N
2951	2951	221	1	2026-10-08	purchase	\N	\N
2952	2952	221	1	2026-10-08	purchase	\N	\N
2953	2953	221	1	2026-10-08	purchase	\N	\N
2954	2954	221	1	2026-10-08	purchase	\N	\N
2955	2955	221	1	2026-10-08	purchase	\N	\N
2956	2956	221	1	2026-10-08	purchase	\N	\N
2957	2957	221	1	2026-10-08	donation	\N	\N
2958	2958	221	1	2026-10-08	purchase	\N	\N
2959	2959	222	1	2026-10-08	purchase	\N	\N
2960	2960	222	1	2026-10-08	purchase	\N	\N
2961	2961	222	1	2026-10-08	purchase	\N	\N
2962	2962	222	1	2026-10-08	donation	\N	\N
2963	2963	222	1	2026-10-08	purchase	\N	\N
2964	2964	222	1	2026-10-08	purchase	\N	\N
2965	2965	222	1	2026-10-08	purchase	\N	\N
2966	2966	222	1	2026-10-08	purchase	\N	\N
2967	2967	222	1	2026-10-08	purchase	\N	\N
2968	2968	222	1	2026-10-08	purchase	\N	\N
2969	2969	222	1	2026-10-08	donation	\N	\N
2970	2970	223	1	2026-10-08	purchase	\N	\N
2971	2971	223	1	2026-10-08	purchase	\N	\N
2972	2972	223	1	2026-10-08	donation	\N	\N
2973	2973	223	1	2026-10-08	purchase	\N	\N
2974	2974	223	1	2026-10-08	purchase	\N	\N
2975	2975	223	1	2026-10-08	purchase	\N	\N
2976	2976	223	1	2026-10-08	purchase	\N	\N
2977	2977	223	1	2026-10-08	purchase	\N	\N
2978	2978	223	1	2026-10-08	purchase	\N	\N
2979	2979	224	1	2026-10-08	purchase	\N	\N
2980	2980	224	1	2026-10-08	donation	\N	\N
2981	2981	224	1	2026-10-08	purchase	\N	\N
2982	2982	224	1	2026-10-08	purchase	\N	\N
2983	2983	224	1	2026-10-08	purchase	\N	\N
2984	2984	224	1	2026-10-08	purchase	\N	\N
2985	2985	224	1	2026-10-08	purchase	\N	\N
2986	2986	224	1	2026-10-08	purchase	\N	\N
2987	2987	224	1	2026-10-08	donation	\N	\N
2988	2988	224	1	2026-10-08	purchase	\N	\N
2989	2989	224	1	2026-10-08	purchase	\N	\N
2990	2990	225	1	2026-10-08	donation	\N	\N
2991	2991	225	1	2026-10-08	purchase	\N	\N
2992	2992	225	1	2026-10-08	purchase	\N	\N
2993	2993	225	1	2026-10-08	purchase	\N	\N
2994	2994	225	1	2026-10-08	purchase	\N	\N
2995	2995	225	1	2026-10-08	purchase	\N	\N
2996	2996	225	1	2026-10-08	purchase	\N	\N
2997	2997	225	1	2026-10-08	donation	\N	\N
2998	2998	225	1	2026-10-08	purchase	\N	\N
2999	2999	226	1	2026-10-08	purchase	\N	\N
3000	3000	226	1	2026-10-08	purchase	\N	\N
3001	3001	226	1	2026-10-08	purchase	\N	\N
3002	3002	226	1	2026-10-08	purchase	\N	\N
3003	3003	226	1	2026-10-08	purchase	\N	\N
3004	3004	226	1	2026-10-08	purchase	\N	\N
3005	3005	226	1	2026-10-08	donation	\N	\N
3006	3006	226	1	2026-10-08	purchase	\N	\N
3007	3007	226	1	2026-10-08	purchase	\N	\N
3008	3008	226	1	2026-10-08	purchase	\N	\N
3009	3009	226	1	2026-10-08	purchase	\N	\N
3010	3010	227	1	2026-10-08	purchase	\N	\N
3011	3011	227	1	2026-10-08	purchase	\N	\N
3012	3012	227	1	2026-10-08	purchase	\N	\N
3013	3013	227	1	2026-10-08	purchase	\N	\N
3014	3014	227	1	2026-10-08	purchase	\N	\N
3015	3015	227	1	2026-10-08	donation	\N	\N
3016	3016	227	1	2026-10-08	purchase	\N	\N
3017	3017	227	1	2026-10-08	purchase	\N	\N
3018	3018	227	1	2026-10-08	purchase	\N	\N
3019	3019	228	1	2026-10-08	purchase	\N	\N
3020	3020	228	1	2026-10-08	purchase	\N	\N
3021	3021	228	1	2026-10-08	purchase	\N	\N
3022	3022	228	1	2026-10-08	purchase	\N	\N
3023	3023	228	1	2026-10-08	donation	\N	\N
3024	3024	228	1	2026-10-08	purchase	\N	\N
3025	3025	228	1	2026-10-08	purchase	\N	\N
3026	3026	228	1	2026-10-08	purchase	\N	\N
3027	3027	228	1	2026-10-08	purchase	\N	\N
3028	3028	228	1	2026-10-08	purchase	\N	\N
3029	3029	228	1	2026-10-08	purchase	\N	\N
3030	3030	228	1	2026-10-08	donation	\N	\N
3031	3031	228	1	2026-10-08	purchase	\N	\N
3032	3032	228	1	2026-10-08	purchase	\N	\N
3033	3033	228	1	2026-10-08	purchase	\N	\N
3034	3034	229	1	2026-10-08	purchase	\N	\N
3035	3035	229	1	2026-10-08	purchase	\N	\N
3036	3036	229	1	2026-10-08	purchase	\N	\N
3037	3037	229	1	2026-10-08	donation	\N	\N
3038	3038	229	1	2026-10-08	purchase	\N	\N
3039	3039	229	1	2026-10-08	purchase	\N	\N
3040	3040	229	1	2026-10-08	purchase	\N	\N
3041	3041	229	1	2026-10-08	purchase	\N	\N
3042	3042	229	1	2026-10-08	purchase	\N	\N
3043	3043	229	1	2026-10-08	purchase	\N	\N
3044	3044	229	1	2026-10-08	donation	\N	\N
3045	3045	229	1	2026-10-08	purchase	\N	\N
3046	3046	229	1	2026-10-08	purchase	\N	\N
3047	3047	230	1	2026-10-08	purchase	\N	\N
3048	3048	230	1	2026-10-08	purchase	\N	\N
3049	3049	230	1	2026-10-08	donation	\N	\N
3050	3050	230	1	2026-10-08	purchase	\N	\N
3051	3051	230	1	2026-10-08	purchase	\N	\N
3052	3052	230	1	2026-10-08	purchase	\N	\N
3053	3053	230	1	2026-10-08	purchase	\N	\N
3054	3054	230	1	2026-10-08	purchase	\N	\N
3055	3055	230	1	2026-10-08	purchase	\N	\N
3056	3056	230	1	2026-10-08	donation	\N	\N
3057	3057	230	1	2026-10-08	purchase	\N	\N
3058	3058	230	1	2026-10-08	purchase	\N	\N
3059	3059	230	1	2026-10-08	purchase	\N	\N
3060	3060	231	1	2026-10-08	purchase	\N	\N
3061	3061	231	1	2026-10-08	donation	\N	\N
3062	3062	231	1	2026-10-08	purchase	\N	\N
3063	3063	231	1	2026-10-08	purchase	\N	\N
3064	3064	231	1	2026-10-08	purchase	\N	\N
3065	3065	231	1	2026-10-08	purchase	\N	\N
3066	3066	231	1	2026-10-08	purchase	\N	\N
3067	3067	231	1	2026-10-08	purchase	\N	\N
3068	3068	231	1	2026-10-08	donation	\N	\N
3069	3069	232	1	2026-10-08	donation	\N	\N
3070	3070	232	1	2026-10-08	purchase	\N	\N
3071	3071	232	1	2026-10-08	purchase	\N	\N
3072	3072	232	1	2026-10-08	purchase	\N	\N
3073	3073	232	1	2026-10-08	purchase	\N	\N
3074	3074	232	1	2026-10-08	purchase	\N	\N
3075	3075	232	1	2026-10-08	purchase	\N	\N
3076	3076	232	1	2026-10-08	donation	\N	\N
3077	3077	232	1	2026-10-08	purchase	\N	\N
3078	3078	232	1	2026-10-08	purchase	\N	\N
3079	3079	232	1	2026-10-08	purchase	\N	\N
3080	3080	232	1	2026-10-08	purchase	\N	\N
3081	3081	232	1	2026-10-08	purchase	\N	\N
3082	3082	232	1	2026-10-08	purchase	\N	\N
3083	3083	232	1	2026-10-08	donation	\N	\N
3084	3084	233	1	2026-10-08	purchase	\N	\N
3085	3085	233	1	2026-10-08	purchase	\N	\N
3086	3086	233	1	2026-10-08	purchase	\N	\N
3087	3087	233	1	2026-10-08	purchase	\N	\N
3088	3088	233	1	2026-10-08	purchase	\N	\N
3089	3089	233	1	2026-10-08	purchase	\N	\N
3090	3090	233	1	2026-10-08	donation	\N	\N
3091	3091	233	1	2026-10-08	purchase	\N	\N
3092	3092	233	1	2026-10-08	purchase	\N	\N
3093	3093	233	1	2026-10-08	purchase	\N	\N
3094	3094	233	1	2026-10-08	purchase	\N	\N
3095	3095	234	1	2026-10-08	purchase	\N	\N
3096	3096	234	1	2026-10-08	purchase	\N	\N
3097	3097	234	1	2026-10-08	purchase	\N	\N
3098	3098	234	1	2026-10-08	purchase	\N	\N
3099	3099	234	1	2026-10-08	purchase	\N	\N
3100	3100	234	1	2026-10-08	donation	\N	\N
3101	3101	234	1	2026-10-08	purchase	\N	\N
3102	3102	234	1	2026-10-08	purchase	\N	\N
3103	3103	234	1	2026-10-08	purchase	\N	\N
3104	3104	235	1	2026-10-08	purchase	\N	\N
3105	3105	235	1	2026-10-08	purchase	\N	\N
3106	3106	235	1	2026-10-08	purchase	\N	\N
3107	3107	235	1	2026-10-08	purchase	\N	\N
3108	3108	235	1	2026-10-08	donation	\N	\N
3109	3109	235	1	2026-10-08	purchase	\N	\N
3110	3110	235	1	2026-10-08	purchase	\N	\N
3111	3111	235	1	2026-10-08	purchase	\N	\N
3112	3112	235	1	2026-10-08	purchase	\N	\N
3113	3113	235	1	2026-10-08	purchase	\N	\N
3114	3114	235	1	2026-10-08	purchase	\N	\N
3115	3115	236	1	2026-10-08	purchase	\N	\N
3116	3116	236	1	2026-10-08	purchase	\N	\N
3117	3117	236	1	2026-10-08	purchase	\N	\N
3118	3118	236	1	2026-10-08	donation	\N	\N
3119	3119	236	1	2026-10-08	purchase	\N	\N
3120	3120	236	1	2026-10-08	purchase	\N	\N
3121	3121	236	1	2026-10-08	purchase	\N	\N
3122	3122	236	1	2026-10-08	purchase	\N	\N
3123	3123	237	1	2026-10-08	purchase	\N	\N
3124	3124	237	1	2026-10-08	purchase	\N	\N
3125	3125	237	1	2026-10-08	donation	\N	\N
3126	3126	237	1	2026-10-08	purchase	\N	\N
3127	3127	237	1	2026-10-08	purchase	\N	\N
3128	3128	237	1	2026-10-08	purchase	\N	\N
3129	3129	237	1	2026-10-08	purchase	\N	\N
3130	3130	237	1	2026-10-08	purchase	\N	\N
3131	3131	237	1	2026-10-08	purchase	\N	\N
3132	3132	237	1	2026-10-08	donation	\N	\N
3133	3133	237	1	2026-10-08	purchase	\N	\N
3134	3134	238	1	2026-10-08	purchase	\N	\N
3135	3135	238	1	2026-10-08	donation	\N	\N
3136	3136	238	1	2026-10-08	purchase	\N	\N
3137	3137	238	1	2026-10-08	purchase	\N	\N
3138	3138	238	1	2026-10-08	purchase	\N	\N
3139	3139	238	1	2026-10-08	purchase	\N	\N
3140	3140	238	1	2026-10-08	purchase	\N	\N
3141	3141	238	1	2026-10-08	purchase	\N	\N
3142	3142	238	1	2026-10-08	donation	\N	\N
3143	3143	239	1	2026-10-08	donation	\N	\N
3144	3144	239	1	2026-10-08	purchase	\N	\N
3145	3145	239	1	2026-10-08	purchase	\N	\N
3146	3146	239	1	2026-10-08	purchase	\N	\N
3147	3147	239	1	2026-10-08	purchase	\N	\N
3148	3148	239	1	2026-10-08	purchase	\N	\N
3149	3149	239	1	2026-10-08	purchase	\N	\N
3150	3150	239	1	2026-10-08	donation	\N	\N
3151	3151	240	1	2026-10-08	purchase	\N	\N
3152	3152	240	1	2026-10-08	purchase	\N	\N
3153	3153	240	1	2026-10-08	purchase	\N	\N
3154	3154	240	1	2026-10-08	purchase	\N	\N
3155	3155	240	1	2026-10-08	purchase	\N	\N
3156	3156	240	1	2026-10-08	purchase	\N	\N
3157	3157	240	1	2026-10-08	donation	\N	\N
3158	3158	240	1	2026-10-08	purchase	\N	\N
3159	3159	241	1	2026-10-08	purchase	\N	\N
3160	3160	241	1	2026-10-08	purchase	\N	\N
3161	3161	241	1	2026-10-08	purchase	\N	\N
3162	3162	241	1	2026-10-08	purchase	\N	\N
3163	3163	241	1	2026-10-08	purchase	\N	\N
3164	3164	241	1	2026-10-08	donation	\N	\N
3165	3165	241	1	2026-10-08	purchase	\N	\N
3166	3166	242	1	2026-10-08	purchase	\N	\N
3167	3167	243	1	2026-10-08	purchase	\N	\N
3168	3168	243	1	2026-10-08	purchase	\N	\N
3169	3169	243	1	2026-10-08	purchase	\N	\N
3170	3170	243	1	2026-10-08	donation	\N	\N
3171	3171	243	1	2026-10-08	purchase	\N	\N
3172	3172	243	1	2026-10-08	purchase	\N	\N
3173	3173	243	1	2026-10-08	purchase	\N	\N
3174	3174	243	1	2026-10-08	purchase	\N	\N
3175	3175	243	1	2026-10-08	purchase	\N	\N
3176	3176	243	1	2026-10-08	purchase	\N	\N
3177	3177	243	1	2026-10-08	donation	\N	\N
3178	3178	243	1	2026-10-08	purchase	\N	\N
3179	3179	243	1	2026-10-08	purchase	\N	\N
3180	3180	243	1	2026-10-08	purchase	\N	\N
3181	3181	243	1	2026-10-08	purchase	\N	\N
3182	3182	243	1	2026-10-08	purchase	\N	\N
3183	3183	243	1	2026-10-08	purchase	\N	\N
3184	3184	243	1	2026-10-08	donation	\N	\N
3185	3185	243	1	2026-10-08	purchase	\N	\N
3186	3186	243	1	2026-10-08	purchase	\N	\N
3187	3187	243	1	2026-10-08	purchase	\N	\N
3188	3188	244	1	2026-10-08	purchase	\N	\N
3189	3189	244	1	2026-10-08	purchase	\N	\N
3190	3190	244	1	2026-10-08	donation	\N	\N
3191	3191	244	1	2026-10-08	purchase	\N	\N
3192	3192	244	1	2026-10-08	purchase	\N	\N
3193	3193	244	1	2026-10-08	purchase	\N	\N
3194	3194	244	1	2026-10-08	purchase	\N	\N
3195	3195	244	1	2026-10-08	purchase	\N	\N
3196	3196	244	1	2026-10-08	purchase	\N	\N
3197	3197	244	1	2026-10-08	donation	\N	\N
3198	3198	244	1	2026-10-08	purchase	\N	\N
3199	3199	244	1	2026-10-08	purchase	\N	\N
3200	3200	244	1	2026-10-08	purchase	\N	\N
3201	3201	244	1	2026-10-08	purchase	\N	\N
3202	3202	244	1	2026-10-08	purchase	\N	\N
3203	3203	244	1	2026-10-08	purchase	\N	\N
3204	3204	244	1	2026-10-08	donation	\N	\N
3205	3205	245	1	2026-10-08	purchase	\N	\N
3206	3206	245	1	2026-10-08	donation	\N	\N
3207	3207	245	1	2026-10-08	purchase	\N	\N
3208	3208	245	1	2026-10-08	purchase	\N	\N
3209	3209	245	1	2026-10-08	purchase	\N	\N
3210	3210	245	1	2026-10-08	purchase	\N	\N
3211	3211	245	1	2026-10-08	purchase	\N	\N
3212	3212	245	1	2026-10-08	purchase	\N	\N
3213	3213	245	1	2026-10-08	donation	\N	\N
3214	3214	245	1	2026-10-08	purchase	\N	\N
3215	3215	245	1	2026-10-08	purchase	\N	\N
3216	3216	245	1	2026-10-08	purchase	\N	\N
3217	3217	245	1	2026-10-08	purchase	\N	\N
3218	3218	245	1	2026-10-08	purchase	\N	\N
3219	3219	245	1	2026-10-08	purchase	\N	\N
3220	3220	246	1	2026-10-08	donation	\N	\N
3221	3221	246	1	2026-10-08	purchase	\N	\N
3222	3222	246	1	2026-10-08	purchase	\N	\N
3223	3223	246	1	2026-10-08	purchase	\N	\N
3224	3224	246	1	2026-10-08	purchase	\N	\N
3225	3225	246	1	2026-10-08	purchase	\N	\N
3226	3226	246	1	2026-10-08	purchase	\N	\N
3227	3227	246	1	2026-10-08	donation	\N	\N
3228	3228	246	1	2026-10-08	purchase	\N	\N
3229	3229	246	1	2026-10-08	purchase	\N	\N
3230	3230	246	1	2026-10-08	purchase	\N	\N
3231	3231	246	1	2026-10-08	purchase	\N	\N
3232	3232	246	1	2026-10-08	purchase	\N	\N
3233	3233	246	1	2026-10-08	purchase	\N	\N
3234	3234	246	1	2026-10-08	donation	\N	\N
3235	3235	246	1	2026-10-08	purchase	\N	\N
3236	3236	246	1	2026-10-08	purchase	\N	\N
3237	3237	247	1	2026-10-08	purchase	\N	\N
3238	3238	247	1	2026-10-08	purchase	\N	\N
3239	3239	247	1	2026-10-08	purchase	\N	\N
3240	3240	247	1	2026-10-08	purchase	\N	\N
3241	3241	247	1	2026-10-08	purchase	\N	\N
3242	3242	247	1	2026-10-08	purchase	\N	\N
3243	3243	247	1	2026-10-08	donation	\N	\N
3244	3244	247	1	2026-10-08	purchase	\N	\N
3245	3245	247	1	2026-10-08	purchase	\N	\N
3246	3246	247	1	2026-10-08	purchase	\N	\N
3247	3247	247	1	2026-10-08	purchase	\N	\N
3248	3248	247	1	2026-10-08	purchase	\N	\N
3249	3249	247	1	2026-10-08	purchase	\N	\N
3250	3250	247	1	2026-10-08	donation	\N	\N
3251	3251	247	1	2026-10-08	purchase	\N	\N
3252	3252	247	1	2026-10-08	purchase	\N	\N
3253	3253	247	1	2026-10-08	purchase	\N	\N
3254	3254	247	1	2026-10-08	purchase	\N	\N
3255	3255	247	1	2026-10-08	purchase	\N	\N
3256	3256	248	1	2026-10-08	purchase	\N	\N
3257	3257	248	1	2026-10-08	purchase	\N	\N
3258	3258	248	1	2026-10-08	purchase	\N	\N
3259	3259	248	1	2026-10-08	purchase	\N	\N
3260	3260	248	1	2026-10-08	purchase	\N	\N
3261	3261	248	1	2026-10-08	donation	\N	\N
3262	3262	248	1	2026-10-08	purchase	\N	\N
3263	3263	248	1	2026-10-08	purchase	\N	\N
3264	3264	248	1	2026-10-08	purchase	\N	\N
3265	3265	248	1	2026-10-08	purchase	\N	\N
3266	3266	248	1	2026-10-08	purchase	\N	\N
3267	3267	248	1	2026-10-08	purchase	\N	\N
3268	3268	248	1	2026-10-08	donation	\N	\N
3269	3269	249	1	2026-10-08	purchase	\N	\N
3270	3270	249	1	2026-10-08	purchase	\N	\N
3271	3271	249	1	2026-10-08	purchase	\N	\N
3272	3272	249	1	2026-10-08	purchase	\N	\N
3273	3273	249	1	2026-10-08	donation	\N	\N
3274	3274	249	1	2026-10-08	purchase	\N	\N
3275	3275	249	1	2026-10-08	purchase	\N	\N
3276	3276	249	1	2026-10-08	purchase	\N	\N
3277	3277	249	1	2026-10-08	purchase	\N	\N
3278	3278	249	1	2026-10-08	purchase	\N	\N
3279	3279	249	1	2026-10-08	purchase	\N	\N
3280	3280	249	1	2026-10-08	donation	\N	\N
3281	3281	249	1	2026-10-08	purchase	\N	\N
3282	3282	249	1	2026-10-08	purchase	\N	\N
3283	3283	249	1	2026-10-08	purchase	\N	\N
3284	3284	249	1	2026-10-08	purchase	\N	\N
3285	3285	249	1	2026-10-08	purchase	\N	\N
3286	3286	250	1	2026-10-08	purchase	\N	\N
3287	3287	250	1	2026-10-08	purchase	\N	\N
3288	3288	250	1	2026-10-08	purchase	\N	\N
3289	3289	250	1	2026-10-08	donation	\N	\N
3290	3290	250	1	2026-10-08	purchase	\N	\N
3291	3291	250	1	2026-10-08	purchase	\N	\N
3292	3292	250	1	2026-10-08	purchase	\N	\N
3293	3293	250	1	2026-10-08	purchase	\N	\N
3294	3294	250	1	2026-10-08	purchase	\N	\N
3295	3295	250	1	2026-10-08	purchase	\N	\N
3296	3296	250	1	2026-10-08	donation	\N	\N
3297	3297	250	1	2026-10-08	purchase	\N	\N
3298	3298	250	1	2026-10-08	purchase	\N	\N
3299	3299	250	1	2026-10-08	purchase	\N	\N
3300	3300	250	1	2026-10-08	purchase	\N	\N
3301	3301	251	1	2026-10-08	purchase	\N	\N
3302	3302	251	1	2026-10-08	purchase	\N	\N
3303	3303	251	1	2026-10-08	donation	\N	\N
3304	3304	251	1	2026-10-08	purchase	\N	\N
3305	3305	251	1	2026-10-08	purchase	\N	\N
3306	3306	251	1	2026-10-08	purchase	\N	\N
3307	3307	251	1	2026-10-08	purchase	\N	\N
3308	3308	251	1	2026-10-08	purchase	\N	\N
3309	3309	251	1	2026-10-08	purchase	\N	\N
3310	3310	251	1	2026-10-08	donation	\N	\N
3311	3311	251	1	2026-10-08	purchase	\N	\N
3312	3312	251	1	2026-10-08	purchase	\N	\N
3313	3313	251	1	2026-10-08	purchase	\N	\N
3314	3314	251	1	2026-10-08	purchase	\N	\N
3315	3315	251	1	2026-10-08	purchase	\N	\N
3316	3316	251	1	2026-10-08	purchase	\N	\N
3317	3317	251	1	2026-10-08	donation	\N	\N
3318	3318	252	1	2026-10-08	purchase	\N	\N
3319	3319	252	1	2026-10-08	donation	\N	\N
3320	3320	252	1	2026-10-08	purchase	\N	\N
3321	3321	252	1	2026-10-08	purchase	\N	\N
3322	3322	252	1	2026-10-08	purchase	\N	\N
3323	3323	252	1	2026-10-08	purchase	\N	\N
3324	3324	252	1	2026-10-08	purchase	\N	\N
3325	3325	252	1	2026-10-08	purchase	\N	\N
3326	3326	252	1	2026-10-08	donation	\N	\N
3327	3327	252	1	2026-10-08	purchase	\N	\N
3328	3328	252	1	2026-10-08	purchase	\N	\N
3329	3329	253	1	2026-10-08	donation	\N	\N
3330	3330	253	1	2026-10-08	purchase	\N	\N
3331	3331	253	1	2026-10-08	purchase	\N	\N
3332	3332	253	1	2026-10-08	purchase	\N	\N
3333	3333	253	1	2026-10-08	purchase	\N	\N
3334	3334	253	1	2026-10-08	purchase	\N	\N
3335	3335	253	1	2026-10-08	purchase	\N	\N
3336	3336	253	1	2026-10-08	donation	\N	\N
3337	3337	253	1	2026-10-08	purchase	\N	\N
3338	3338	253	1	2026-10-08	purchase	\N	\N
3339	3339	253	1	2026-10-08	purchase	\N	\N
3340	3340	254	1	2026-10-08	purchase	\N	\N
3341	3341	254	1	2026-10-08	purchase	\N	\N
3342	3342	254	1	2026-10-08	purchase	\N	\N
3343	3343	254	1	2026-10-08	purchase	\N	\N
3344	3344	254	1	2026-10-08	purchase	\N	\N
3345	3345	254	1	2026-10-08	purchase	\N	\N
3346	3346	254	1	2026-10-08	donation	\N	\N
3347	3347	254	1	2026-10-08	purchase	\N	\N
3348	3348	254	1	2026-10-08	purchase	\N	\N
3349	3349	254	1	2026-10-08	purchase	\N	\N
3350	3350	254	1	2026-10-08	purchase	\N	\N
3351	3351	254	1	2026-10-08	purchase	\N	\N
3352	3352	254	1	2026-10-08	purchase	\N	\N
3353	3353	254	1	2026-10-08	donation	\N	\N
3354	3354	254	1	2026-10-08	purchase	\N	\N
3355	3355	254	1	2026-10-08	purchase	\N	\N
3356	3356	254	1	2026-10-08	purchase	\N	\N
3357	3357	255	1	2026-10-08	purchase	\N	\N
3358	3358	255	1	2026-10-08	purchase	\N	\N
3359	3359	255	1	2026-10-08	purchase	\N	\N
3360	3360	255	1	2026-10-08	purchase	\N	\N
3361	3361	255	1	2026-10-08	purchase	\N	\N
3362	3362	255	1	2026-10-08	donation	\N	\N
3363	3363	255	1	2026-10-08	purchase	\N	\N
3364	3364	255	1	2026-10-08	purchase	\N	\N
3365	3365	255	1	2026-10-08	purchase	\N	\N
3366	3366	255	1	2026-10-08	purchase	\N	\N
3367	3367	255	1	2026-10-08	purchase	\N	\N
3368	3368	256	1	2026-10-08	purchase	\N	\N
3369	3369	256	1	2026-10-08	purchase	\N	\N
3370	3370	256	1	2026-10-08	purchase	\N	\N
3371	3371	256	1	2026-10-08	purchase	\N	\N
3372	3372	256	1	2026-10-08	donation	\N	\N
3373	3373	256	1	2026-10-08	purchase	\N	\N
3374	3374	256	1	2026-10-08	purchase	\N	\N
3375	3375	256	1	2026-10-08	purchase	\N	\N
3376	3376	256	1	2026-10-08	purchase	\N	\N
3377	3377	256	1	2026-10-08	purchase	\N	\N
3378	3378	256	1	2026-10-08	purchase	\N	\N
3379	3379	257	1	2026-10-08	purchase	\N	\N
3380	3380	257	1	2026-10-08	purchase	\N	\N
3381	3381	257	1	2026-10-08	purchase	\N	\N
3382	3382	257	1	2026-10-08	donation	\N	\N
3383	3383	257	1	2026-10-08	purchase	\N	\N
3384	3384	257	1	2026-10-08	purchase	\N	\N
3385	3385	257	1	2026-10-08	purchase	\N	\N
3386	3386	257	1	2026-10-08	purchase	\N	\N
3387	3387	257	1	2026-10-08	purchase	\N	\N
3388	3388	257	1	2026-10-08	purchase	\N	\N
3389	3389	257	1	2026-10-08	donation	\N	\N
3390	3390	257	1	2026-10-08	purchase	\N	\N
3391	3391	257	1	2026-10-08	purchase	\N	\N
3392	3392	257	1	2026-10-08	purchase	\N	\N
3393	3393	257	1	2026-10-08	purchase	\N	\N
3394	3394	258	1	2026-10-08	purchase	\N	\N
3395	3395	258	1	2026-10-08	purchase	\N	\N
3396	3396	258	1	2026-10-08	donation	\N	\N
3397	3397	258	1	2026-10-08	purchase	\N	\N
3398	3398	258	1	2026-10-08	purchase	\N	\N
3399	3399	258	1	2026-10-08	purchase	\N	\N
3400	3400	258	1	2026-10-08	purchase	\N	\N
3401	3401	258	1	2026-10-08	purchase	\N	\N
3402	3402	258	1	2026-10-08	purchase	\N	\N
3403	3403	258	1	2026-10-08	donation	\N	\N
3404	3404	258	1	2026-10-08	purchase	\N	\N
3405	3405	259	1	2026-10-08	purchase	\N	\N
3406	3406	259	1	2026-10-08	donation	\N	\N
3407	3407	259	1	2026-10-08	purchase	\N	\N
3408	3408	259	1	2026-10-08	purchase	\N	\N
3409	3409	259	1	2026-10-08	purchase	\N	\N
3410	3410	259	1	2026-10-08	purchase	\N	\N
3411	3411	259	1	2026-10-08	purchase	\N	\N
3412	3412	259	1	2026-10-08	purchase	\N	\N
3413	3413	259	1	2026-10-08	donation	\N	\N
3414	3414	259	1	2026-10-08	purchase	\N	\N
3415	3415	259	1	2026-10-08	purchase	\N	\N
3416	3416	259	1	2026-10-08	purchase	\N	\N
3417	3417	259	1	2026-10-08	purchase	\N	\N
3418	3418	260	1	2026-10-08	donation	\N	\N
3419	3419	260	1	2026-10-08	purchase	\N	\N
3420	3420	260	1	2026-10-08	purchase	\N	\N
3421	3421	260	1	2026-10-08	purchase	\N	\N
3422	3422	260	1	2026-10-08	purchase	\N	\N
3423	3423	260	1	2026-10-08	purchase	\N	\N
3424	3424	260	1	2026-10-08	purchase	\N	\N
3425	3425	260	1	2026-10-08	donation	\N	\N
3426	3426	260	1	2026-10-08	purchase	\N	\N
3427	3427	260	1	2026-10-08	purchase	\N	\N
3428	3428	260	1	2026-10-08	purchase	\N	\N
3429	3429	260	1	2026-10-08	purchase	\N	\N
3430	3430	260	1	2026-10-08	purchase	\N	\N
3431	3431	261	1	2026-10-08	purchase	\N	\N
3432	3432	261	1	2026-10-08	purchase	\N	\N
3433	3433	261	1	2026-10-08	purchase	\N	\N
3434	3434	261	1	2026-10-08	purchase	\N	\N
3435	3435	261	1	2026-10-08	purchase	\N	\N
3436	3436	261	1	2026-10-08	purchase	\N	\N
3437	3437	261	1	2026-10-08	donation	\N	\N
3438	3438	261	1	2026-10-08	purchase	\N	\N
3439	3439	261	1	2026-10-08	purchase	\N	\N
3440	3440	261	1	2026-10-08	purchase	\N	\N
3441	3441	261	1	2026-10-08	purchase	\N	\N
3442	3442	262	1	2026-10-08	purchase	\N	\N
3443	3443	262	1	2026-10-08	purchase	\N	\N
3444	3444	262	1	2026-10-08	purchase	\N	\N
3445	3445	262	1	2026-10-08	purchase	\N	\N
3446	3446	262	1	2026-10-08	purchase	\N	\N
3447	3447	262	1	2026-10-08	donation	\N	\N
3448	3448	262	1	2026-10-08	purchase	\N	\N
3449	3449	262	1	2026-10-08	purchase	\N	\N
3450	3450	262	1	2026-10-08	purchase	\N	\N
3451	3451	262	1	2026-10-08	purchase	\N	\N
3452	3452	262	1	2026-10-08	purchase	\N	\N
3453	3453	262	1	2026-10-08	purchase	\N	\N
3454	3454	262	1	2026-10-08	donation	\N	\N
3455	3455	263	1	2026-10-08	purchase	\N	\N
3456	3456	263	1	2026-10-08	purchase	\N	\N
3457	3457	263	1	2026-10-08	purchase	\N	\N
3458	3458	263	1	2026-10-08	purchase	\N	\N
3459	3459	263	1	2026-10-08	donation	\N	\N
3460	3460	263	1	2026-10-08	purchase	\N	\N
3461	3461	263	1	2026-10-08	purchase	\N	\N
3462	3462	263	1	2026-10-08	purchase	\N	\N
3463	3463	263	1	2026-10-08	purchase	\N	\N
3464	3464	263	1	2026-10-08	purchase	\N	\N
3465	3465	263	1	2026-10-08	purchase	\N	\N
3466	3466	263	1	2026-10-08	donation	\N	\N
3467	3467	263	1	2026-10-08	purchase	\N	\N
3468	3468	264	1	2026-10-08	purchase	\N	\N
3469	3469	264	1	2026-10-08	purchase	\N	\N
3470	3470	264	1	2026-10-08	purchase	\N	\N
3471	3471	264	1	2026-10-08	donation	\N	\N
3472	3472	264	1	2026-10-08	purchase	\N	\N
3473	3473	264	1	2026-10-08	purchase	\N	\N
3474	3474	264	1	2026-10-08	purchase	\N	\N
3475	3475	264	1	2026-10-08	purchase	\N	\N
3476	3476	264	1	2026-10-08	purchase	\N	\N
3477	3477	264	1	2026-10-08	purchase	\N	\N
3478	3478	264	1	2026-10-08	donation	\N	\N
3479	3479	265	1	2026-10-08	purchase	\N	\N
3480	3480	265	1	2026-10-08	purchase	\N	\N
3481	3481	265	1	2026-10-08	donation	\N	\N
3482	3482	265	1	2026-10-08	purchase	\N	\N
3483	3483	265	1	2026-10-08	purchase	\N	\N
3484	3484	265	1	2026-10-08	purchase	\N	\N
3485	3485	265	1	2026-10-08	purchase	\N	\N
3486	3486	265	1	2026-10-08	purchase	\N	\N
3487	3487	265	1	2026-10-08	purchase	\N	\N
3488	3488	266	1	2026-10-08	purchase	\N	\N
3489	3489	266	1	2026-10-08	donation	\N	\N
3490	3490	266	1	2026-10-08	purchase	\N	\N
3491	3491	266	1	2026-10-08	purchase	\N	\N
3492	3492	266	1	2026-10-08	purchase	\N	\N
3493	3493	266	1	2026-10-08	purchase	\N	\N
3494	3494	266	1	2026-10-08	purchase	\N	\N
3495	3495	266	1	2026-10-08	purchase	\N	\N
3496	3496	266	1	2026-10-08	donation	\N	\N
3497	3497	267	1	2026-10-08	donation	\N	\N
3498	3498	267	1	2026-10-08	purchase	\N	\N
3499	3499	267	1	2026-10-08	purchase	\N	\N
3500	3500	267	1	2026-10-08	purchase	\N	\N
3501	3501	267	1	2026-10-08	purchase	\N	\N
3502	3502	267	1	2026-10-08	purchase	\N	\N
3503	3503	267	1	2026-10-08	purchase	\N	\N
3504	3504	267	1	2026-10-08	donation	\N	\N
3505	3505	268	1	2026-10-08	purchase	\N	\N
3506	3506	268	1	2026-10-08	purchase	\N	\N
3507	3507	268	1	2026-10-08	purchase	\N	\N
3508	3508	268	1	2026-10-08	purchase	\N	\N
3509	3509	268	1	2026-10-08	purchase	\N	\N
3510	3510	268	1	2026-10-08	purchase	\N	\N
3511	3511	268	1	2026-10-08	donation	\N	\N
3512	3512	268	1	2026-10-08	purchase	\N	\N
3513	3513	268	1	2026-10-08	purchase	\N	\N
3514	3514	269	1	2026-10-08	purchase	\N	\N
3515	3515	269	1	2026-10-08	purchase	\N	\N
3516	3516	269	1	2026-10-08	purchase	\N	\N
3517	3517	269	1	2026-10-08	purchase	\N	\N
3518	3518	269	1	2026-10-08	purchase	\N	\N
3519	3519	269	1	2026-10-08	donation	\N	\N
3520	3520	269	1	2026-10-08	purchase	\N	\N
3521	3521	269	1	2026-10-08	purchase	\N	\N
3522	3522	270	1	2026-10-08	purchase	\N	\N
3523	3523	270	1	2026-10-08	purchase	\N	\N
3524	3524	270	1	2026-10-08	purchase	\N	\N
3525	3525	270	1	2026-10-08	purchase	\N	\N
3526	3526	270	1	2026-10-08	donation	\N	\N
3527	3527	270	1	2026-10-08	purchase	\N	\N
3528	3528	270	1	2026-10-08	purchase	\N	\N
3529	3529	270	1	2026-10-08	purchase	\N	\N
3530	3530	271	1	2026-10-08	purchase	\N	\N
3531	3531	271	1	2026-10-08	purchase	\N	\N
3532	3532	271	1	2026-10-08	purchase	\N	\N
3533	3533	271	1	2026-10-08	donation	\N	\N
3534	3534	271	1	2026-10-08	purchase	\N	\N
3535	3535	271	1	2026-10-08	purchase	\N	\N
3536	3536	271	1	2026-10-08	purchase	\N	\N
3537	3537	271	1	2026-10-08	purchase	\N	\N
3538	3538	271	1	2026-10-08	purchase	\N	\N
3539	3539	271	1	2026-10-08	purchase	\N	\N
3540	3540	271	1	2026-10-08	donation	\N	\N
3541	3541	272	1	2026-10-08	purchase	\N	\N
3542	3542	272	1	2026-10-08	purchase	\N	\N
3543	3543	272	1	2026-10-08	donation	\N	\N
3544	3544	272	1	2026-10-08	purchase	\N	\N
3545	3545	272	1	2026-10-08	purchase	\N	\N
3546	3546	272	1	2026-10-08	purchase	\N	\N
3547	3547	272	1	2026-10-08	purchase	\N	\N
3548	3548	272	1	2026-10-08	purchase	\N	\N
3549	3549	272	1	2026-10-08	purchase	\N	\N
3550	3550	273	1	2026-10-08	purchase	\N	\N
3551	3551	273	1	2026-10-08	donation	\N	\N
3552	3552	273	1	2026-10-08	purchase	\N	\N
3553	3553	273	1	2026-10-08	purchase	\N	\N
3554	3554	273	1	2026-10-08	purchase	\N	\N
3555	3555	273	1	2026-10-08	purchase	\N	\N
3556	3556	273	1	2026-10-08	purchase	\N	\N
3557	3557	273	1	2026-10-08	purchase	\N	\N
3558	3558	273	1	2026-10-08	donation	\N	\N
3559	3559	274	1	2026-10-08	donation	\N	\N
3560	3560	274	1	2026-10-08	purchase	\N	\N
3561	3561	274	1	2026-10-08	purchase	\N	\N
3562	3562	274	1	2026-10-08	purchase	\N	\N
3563	3563	274	1	2026-10-08	purchase	\N	\N
3564	3564	274	1	2026-10-08	purchase	\N	\N
3565	3565	274	1	2026-10-08	purchase	\N	\N
3566	3566	275	1	2026-10-08	purchase	\N	\N
3567	3567	275	1	2026-10-08	purchase	\N	\N
3568	3568	275	1	2026-10-08	purchase	\N	\N
3569	3569	275	1	2026-10-08	purchase	\N	\N
3570	3570	275	1	2026-10-08	purchase	\N	\N
3571	3571	275	1	2026-10-08	purchase	\N	\N
3572	3572	275	1	2026-10-08	donation	\N	\N
3573	3573	275	1	2026-10-08	purchase	\N	\N
3574	3574	275	1	2026-10-08	purchase	\N	\N
3575	3575	275	1	2026-10-08	purchase	\N	\N
3576	3576	275	1	2026-10-08	purchase	\N	\N
3577	3577	276	1	2026-10-08	purchase	\N	\N
3578	3578	276	1	2026-10-08	purchase	\N	\N
3579	3579	276	1	2026-10-08	purchase	\N	\N
3580	3580	276	1	2026-10-08	purchase	\N	\N
3581	3581	276	1	2026-10-08	purchase	\N	\N
3582	3582	276	1	2026-10-08	donation	\N	\N
3583	3583	276	1	2026-10-08	purchase	\N	\N
3584	3584	277	1	2026-10-08	purchase	\N	\N
3585	3585	277	1	2026-10-08	purchase	\N	\N
3586	3586	277	1	2026-10-08	purchase	\N	\N
3587	3587	277	1	2026-10-08	purchase	\N	\N
3588	3588	277	1	2026-10-08	donation	\N	\N
3589	3589	277	1	2026-10-08	purchase	\N	\N
3590	3590	277	1	2026-10-08	purchase	\N	\N
3591	3591	277	1	2026-10-08	purchase	\N	\N
3592	3592	277	1	2026-10-08	purchase	\N	\N
3593	3593	277	1	2026-10-08	purchase	\N	\N
3594	3594	277	1	2026-10-08	purchase	\N	\N
3595	3595	278	1	2026-10-08	purchase	\N	\N
3596	3596	278	1	2026-10-08	purchase	\N	\N
3597	3597	278	1	2026-10-08	purchase	\N	\N
3598	3598	278	1	2026-10-08	donation	\N	\N
3599	3599	278	1	2026-10-08	purchase	\N	\N
3600	3600	278	1	2026-10-08	purchase	\N	\N
3601	3601	278	1	2026-10-08	purchase	\N	\N
3602	3602	278	1	2026-10-08	purchase	\N	\N
3603	3603	278	1	2026-10-08	purchase	\N	\N
3604	3604	278	1	2026-10-08	purchase	\N	\N
3605	3605	278	1	2026-10-08	donation	\N	\N
3606	3606	278	1	2026-10-08	purchase	\N	\N
3607	3607	278	1	2026-10-08	purchase	\N	\N
3608	3608	279	1	2026-10-08	purchase	\N	\N
3609	3609	279	1	2026-10-08	purchase	\N	\N
3610	3610	279	1	2026-10-08	donation	\N	\N
3611	3611	279	1	2026-10-08	purchase	\N	\N
3612	3612	279	1	2026-10-08	purchase	\N	\N
3613	3613	279	1	2026-10-08	purchase	\N	\N
3614	3614	279	1	2026-10-08	purchase	\N	\N
3615	3615	279	1	2026-10-08	purchase	\N	\N
3616	3616	280	1	2026-10-08	purchase	\N	\N
3617	3617	280	1	2026-10-08	donation	\N	\N
3618	3618	280	1	2026-10-08	purchase	\N	\N
3619	3619	280	1	2026-10-08	purchase	\N	\N
3620	3620	280	1	2026-10-08	purchase	\N	\N
3621	3621	280	1	2026-10-08	purchase	\N	\N
3622	3622	280	1	2026-10-08	purchase	\N	\N
3623	3623	280	1	2026-10-08	purchase	\N	\N
3624	3624	281	1	2026-10-08	donation	\N	\N
3625	3625	281	1	2026-10-08	purchase	\N	\N
3626	3626	281	1	2026-10-08	purchase	\N	\N
3627	3627	281	1	2026-10-08	purchase	\N	\N
3628	3628	281	1	2026-10-08	purchase	\N	\N
3629	3629	281	1	2026-10-08	purchase	\N	\N
3630	3630	281	1	2026-10-08	purchase	\N	\N
3631	3631	281	1	2026-10-08	donation	\N	\N
3632	3632	281	1	2026-10-08	purchase	\N	\N
3633	3633	281	1	2026-10-08	purchase	\N	\N
3634	3634	281	1	2026-10-08	purchase	\N	\N
3635	3635	282	1	2026-10-08	purchase	\N	\N
3636	3636	282	1	2026-10-08	purchase	\N	\N
3637	3637	282	1	2026-10-08	purchase	\N	\N
3638	3638	282	1	2026-10-08	purchase	\N	\N
3639	3639	282	1	2026-10-08	purchase	\N	\N
3640	3640	282	1	2026-10-08	purchase	\N	\N
3641	3641	282	1	2026-10-08	donation	\N	\N
3642	3642	282	1	2026-10-08	purchase	\N	\N
3643	3643	282	1	2026-10-08	purchase	\N	\N
3644	3644	283	1	2026-10-08	purchase	\N	\N
3645	3645	283	1	2026-10-08	purchase	\N	\N
3646	3646	283	1	2026-10-08	purchase	\N	\N
3647	3647	283	1	2026-10-08	purchase	\N	\N
3648	3648	283	1	2026-10-08	purchase	\N	\N
3649	3649	283	1	2026-10-08	donation	\N	\N
3650	3650	283	1	2026-10-08	purchase	\N	\N
3651	3651	283	1	2026-10-08	purchase	\N	\N
3652	3652	283	1	2026-10-08	purchase	\N	\N
3653	3653	283	1	2026-10-08	purchase	\N	\N
3654	3654	283	1	2026-10-08	purchase	\N	\N
3655	3655	284	1	2026-10-08	purchase	\N	\N
3656	3656	284	1	2026-10-08	purchase	\N	\N
3657	3657	284	1	2026-10-08	purchase	\N	\N
3658	3658	284	1	2026-10-08	purchase	\N	\N
3659	3659	284	1	2026-10-08	donation	\N	\N
3660	3660	284	1	2026-10-08	purchase	\N	\N
3661	3661	284	1	2026-10-08	purchase	\N	\N
3662	3662	285	1	2026-10-08	purchase	\N	\N
3663	3663	285	1	2026-10-08	purchase	\N	\N
3664	3664	285	1	2026-10-08	purchase	\N	\N
3665	3665	285	1	2026-10-08	donation	\N	\N
3666	3666	285	1	2026-10-08	purchase	\N	\N
3667	3667	285	1	2026-10-08	purchase	\N	\N
3668	3668	285	1	2026-10-08	purchase	\N	\N
3669	3669	286	1	2026-10-08	purchase	\N	\N
3670	3670	287	1	2026-10-08	purchase	\N	\N
3671	3671	287	1	2026-10-08	donation	\N	\N
3672	3672	287	1	2026-10-08	purchase	\N	\N
3673	3673	287	1	2026-10-08	purchase	\N	\N
3674	3674	287	1	2026-10-08	purchase	\N	\N
3675	3675	287	1	2026-10-08	purchase	\N	\N
3676	3676	287	1	2026-10-08	purchase	\N	\N
3677	3677	287	1	2026-10-08	purchase	\N	\N
3678	3678	287	1	2026-10-08	donation	\N	\N
3679	3679	287	1	2026-10-08	purchase	\N	\N
3680	3680	287	1	2026-10-08	purchase	\N	\N
3681	3681	287	1	2026-10-08	purchase	\N	\N
3682	3682	287	1	2026-10-08	purchase	\N	\N
3683	3683	287	1	2026-10-08	purchase	\N	\N
3684	3684	287	1	2026-10-08	purchase	\N	\N
3685	3685	287	1	2026-10-08	donation	\N	\N
3686	3686	287	1	2026-10-08	purchase	\N	\N
3687	3687	287	1	2026-10-08	purchase	\N	\N
3688	3688	287	1	2026-10-08	purchase	\N	\N
3689	3689	287	1	2026-10-08	purchase	\N	\N
3690	3690	287	1	2026-10-08	purchase	\N	\N
3691	3691	287	1	2026-10-08	purchase	\N	\N
3692	3692	287	1	2026-10-08	donation	\N	\N
3693	3693	288	1	2026-10-08	donation	\N	\N
3694	3694	288	1	2026-10-08	purchase	\N	\N
3695	3695	288	1	2026-10-08	purchase	\N	\N
3696	3696	288	1	2026-10-08	purchase	\N	\N
3697	3697	288	1	2026-10-08	purchase	\N	\N
3698	3698	288	1	2026-10-08	purchase	\N	\N
3699	3699	288	1	2026-10-08	purchase	\N	\N
3700	3700	288	1	2026-10-08	donation	\N	\N
3701	3701	288	1	2026-10-08	purchase	\N	\N
3702	3702	288	1	2026-10-08	purchase	\N	\N
3703	3703	288	1	2026-10-08	purchase	\N	\N
3704	3704	288	1	2026-10-08	purchase	\N	\N
3705	3705	288	1	2026-10-08	purchase	\N	\N
3706	3706	288	1	2026-10-08	purchase	\N	\N
3707	3707	288	1	2026-10-08	donation	\N	\N
3708	3708	288	1	2026-10-08	purchase	\N	\N
3709	3709	288	1	2026-10-08	purchase	\N	\N
3710	3710	288	1	2026-10-08	purchase	\N	\N
3711	3711	288	1	2026-10-08	purchase	\N	\N
3712	3712	289	1	2026-10-08	purchase	\N	\N
3713	3713	289	1	2026-10-08	purchase	\N	\N
3714	3714	289	1	2026-10-08	purchase	\N	\N
3715	3715	289	1	2026-10-08	purchase	\N	\N
3716	3716	289	1	2026-10-08	purchase	\N	\N
3717	3717	289	1	2026-10-08	purchase	\N	\N
3718	3718	289	1	2026-10-08	donation	\N	\N
3719	3719	289	1	2026-10-08	purchase	\N	\N
3720	3720	289	1	2026-10-08	purchase	\N	\N
3721	3721	289	1	2026-10-08	purchase	\N	\N
3722	3722	289	1	2026-10-08	purchase	\N	\N
3723	3723	289	1	2026-10-08	purchase	\N	\N
3724	3724	289	1	2026-10-08	purchase	\N	\N
3725	3725	289	1	2026-10-08	donation	\N	\N
3726	3726	289	1	2026-10-08	purchase	\N	\N
3727	3727	289	1	2026-10-08	purchase	\N	\N
3728	3728	289	1	2026-10-08	purchase	\N	\N
3729	3729	289	1	2026-10-08	purchase	\N	\N
3730	3730	289	1	2026-10-08	purchase	\N	\N
3731	3731	289	1	2026-10-08	purchase	\N	\N
3732	3732	289	1	2026-10-08	donation	\N	\N
3733	3733	290	1	2026-10-08	purchase	\N	\N
3734	3734	290	1	2026-10-08	purchase	\N	\N
3735	3735	290	1	2026-10-08	purchase	\N	\N
3736	3736	290	1	2026-10-08	purchase	\N	\N
3737	3737	290	1	2026-10-08	purchase	\N	\N
3738	3738	290	1	2026-10-08	donation	\N	\N
3739	3739	290	1	2026-10-08	purchase	\N	\N
3740	3740	290	1	2026-10-08	purchase	\N	\N
3741	3741	290	1	2026-10-08	purchase	\N	\N
3742	3742	290	1	2026-10-08	purchase	\N	\N
3743	3743	290	1	2026-10-08	purchase	\N	\N
3744	3744	290	1	2026-10-08	purchase	\N	\N
3745	3745	290	1	2026-10-08	donation	\N	\N
3746	3746	290	1	2026-10-08	purchase	\N	\N
3747	3747	290	1	2026-10-08	purchase	\N	\N
3748	3748	290	1	2026-10-08	purchase	\N	\N
3749	3749	290	1	2026-10-08	purchase	\N	\N
3750	3750	290	1	2026-10-08	purchase	\N	\N
3751	3751	290	1	2026-10-08	purchase	\N	\N
3752	3752	291	1	2026-10-08	purchase	\N	\N
3753	3753	291	1	2026-10-08	purchase	\N	\N
3754	3754	291	1	2026-10-08	purchase	\N	\N
3755	3755	291	1	2026-10-08	purchase	\N	\N
3756	3756	291	1	2026-10-08	donation	\N	\N
3757	3757	291	1	2026-10-08	purchase	\N	\N
3758	3758	291	1	2026-10-08	purchase	\N	\N
3759	3759	291	1	2026-10-08	purchase	\N	\N
3760	3760	291	1	2026-10-08	purchase	\N	\N
3761	3761	291	1	2026-10-08	purchase	\N	\N
3762	3762	291	1	2026-10-08	purchase	\N	\N
3763	3763	291	1	2026-10-08	donation	\N	\N
3764	3764	291	1	2026-10-08	purchase	\N	\N
3765	3765	291	1	2026-10-08	purchase	\N	\N
3766	3766	291	1	2026-10-08	purchase	\N	\N
3767	3767	291	1	2026-10-08	purchase	\N	\N
3768	3768	291	1	2026-10-08	purchase	\N	\N
3769	3769	291	1	2026-10-08	purchase	\N	\N
3770	3770	291	1	2026-10-08	donation	\N	\N
3771	3771	291	1	2026-10-08	purchase	\N	\N
3772	3772	291	1	2026-10-08	purchase	\N	\N
3773	3773	291	1	2026-10-08	purchase	\N	\N
3774	3774	291	1	2026-10-08	purchase	\N	\N
3775	3775	292	1	2026-10-08	purchase	\N	\N
3776	3776	292	1	2026-10-08	purchase	\N	\N
3777	3777	292	1	2026-10-08	purchase	\N	\N
3778	3778	292	1	2026-10-08	donation	\N	\N
3779	3779	292	1	2026-10-08	purchase	\N	\N
3780	3780	292	1	2026-10-08	purchase	\N	\N
3781	3781	292	1	2026-10-08	purchase	\N	\N
3782	3782	292	1	2026-10-08	purchase	\N	\N
3783	3783	292	1	2026-10-08	purchase	\N	\N
3784	3784	292	1	2026-10-08	purchase	\N	\N
3785	3785	292	1	2026-10-08	donation	\N	\N
3786	3786	292	1	2026-10-08	purchase	\N	\N
3787	3787	292	1	2026-10-08	purchase	\N	\N
3788	3788	292	1	2026-10-08	purchase	\N	\N
3789	3789	292	1	2026-10-08	purchase	\N	\N
3790	3790	293	1	2026-10-08	purchase	\N	\N
3791	3791	293	1	2026-10-08	purchase	\N	\N
3792	3792	293	1	2026-10-08	donation	\N	\N
3793	3793	293	1	2026-10-08	purchase	\N	\N
3794	3794	293	1	2026-10-08	purchase	\N	\N
3795	3795	293	1	2026-10-08	purchase	\N	\N
3796	3796	293	1	2026-10-08	purchase	\N	\N
3797	3797	293	1	2026-10-08	purchase	\N	\N
3798	3798	293	1	2026-10-08	purchase	\N	\N
3799	3799	293	1	2026-10-08	donation	\N	\N
3800	3800	293	1	2026-10-08	purchase	\N	\N
3801	3801	293	1	2026-10-08	purchase	\N	\N
3802	3802	293	1	2026-10-08	purchase	\N	\N
3803	3803	293	1	2026-10-08	purchase	\N	\N
3804	3804	293	1	2026-10-08	purchase	\N	\N
3805	3805	293	1	2026-10-08	purchase	\N	\N
3806	3806	293	1	2026-10-08	donation	\N	\N
3807	3807	293	1	2026-10-08	purchase	\N	\N
3808	3808	293	1	2026-10-08	purchase	\N	\N
3809	3809	294	1	2026-10-08	purchase	\N	\N
3810	3810	294	1	2026-10-08	donation	\N	\N
3811	3811	294	1	2026-10-08	purchase	\N	\N
3812	3812	294	1	2026-10-08	purchase	\N	\N
3813	3813	294	1	2026-10-08	purchase	\N	\N
3814	3814	294	1	2026-10-08	purchase	\N	\N
3815	3815	294	1	2026-10-08	purchase	\N	\N
3816	3816	294	1	2026-10-08	purchase	\N	\N
3817	3817	294	1	2026-10-08	donation	\N	\N
3818	3818	294	1	2026-10-08	purchase	\N	\N
3819	3819	294	1	2026-10-08	purchase	\N	\N
3820	3820	294	1	2026-10-08	purchase	\N	\N
3821	3821	294	1	2026-10-08	purchase	\N	\N
3822	3822	294	1	2026-10-08	purchase	\N	\N
3823	3823	294	1	2026-10-08	purchase	\N	\N
3824	3824	294	1	2026-10-08	donation	\N	\N
3825	3825	294	1	2026-10-08	purchase	\N	\N
3826	3826	295	1	2026-10-08	donation	\N	\N
3827	3827	295	1	2026-10-08	purchase	\N	\N
3828	3828	295	1	2026-10-08	purchase	\N	\N
3829	3829	295	1	2026-10-08	purchase	\N	\N
3830	3830	295	1	2026-10-08	purchase	\N	\N
3831	3831	295	1	2026-10-08	purchase	\N	\N
3832	3832	295	1	2026-10-08	purchase	\N	\N
3833	3833	295	1	2026-10-08	donation	\N	\N
3834	3834	295	1	2026-10-08	purchase	\N	\N
3835	3835	295	1	2026-10-08	purchase	\N	\N
3836	3836	295	1	2026-10-08	purchase	\N	\N
3837	3837	295	1	2026-10-08	purchase	\N	\N
3838	3838	295	1	2026-10-08	purchase	\N	\N
3839	3839	296	1	2026-10-08	purchase	\N	\N
3840	3840	296	1	2026-10-08	purchase	\N	\N
3841	3841	296	1	2026-10-08	purchase	\N	\N
3842	3842	296	1	2026-10-08	purchase	\N	\N
3843	3843	296	1	2026-10-08	purchase	\N	\N
3844	3844	296	1	2026-10-08	purchase	\N	\N
3845	3845	296	1	2026-10-08	donation	\N	\N
3846	3846	296	1	2026-10-08	purchase	\N	\N
3847	3847	296	1	2026-10-08	purchase	\N	\N
3848	3848	296	1	2026-10-08	purchase	\N	\N
3849	3849	296	1	2026-10-08	purchase	\N	\N
3850	3850	296	1	2026-10-08	purchase	\N	\N
3851	3851	296	1	2026-10-08	purchase	\N	\N
3852	3852	296	1	2026-10-08	donation	\N	\N
3853	3853	296	1	2026-10-08	purchase	\N	\N
3854	3854	296	1	2026-10-08	purchase	\N	\N
3855	3855	296	1	2026-10-08	purchase	\N	\N
3856	3856	296	1	2026-10-08	purchase	\N	\N
3857	3857	296	1	2026-10-08	purchase	\N	\N
3858	3858	297	1	2026-10-08	purchase	\N	\N
3859	3859	297	1	2026-10-08	purchase	\N	\N
3860	3860	297	1	2026-10-08	purchase	\N	\N
3861	3861	297	1	2026-10-08	purchase	\N	\N
3862	3862	297	1	2026-10-08	purchase	\N	\N
3863	3863	297	1	2026-10-08	donation	\N	\N
3864	3864	297	1	2026-10-08	purchase	\N	\N
3865	3865	297	1	2026-10-08	purchase	\N	\N
3866	3866	297	1	2026-10-08	purchase	\N	\N
3867	3867	297	1	2026-10-08	purchase	\N	\N
3868	3868	297	1	2026-10-08	purchase	\N	\N
3869	3869	297	1	2026-10-08	purchase	\N	\N
3870	3870	297	1	2026-10-08	donation	\N	\N
3871	3871	297	1	2026-10-08	purchase	\N	\N
3872	3872	297	1	2026-10-08	purchase	\N	\N
3873	3873	298	1	2026-10-08	purchase	\N	\N
3874	3874	298	1	2026-10-08	purchase	\N	\N
3875	3875	298	1	2026-10-08	purchase	\N	\N
3876	3876	298	1	2026-10-08	purchase	\N	\N
3877	3877	298	1	2026-10-08	donation	\N	\N
3878	3878	298	1	2026-10-08	purchase	\N	\N
3879	3879	298	1	2026-10-08	purchase	\N	\N
3880	3880	298	1	2026-10-08	purchase	\N	\N
3881	3881	298	1	2026-10-08	purchase	\N	\N
3882	3882	298	1	2026-10-08	purchase	\N	\N
3883	3883	298	1	2026-10-08	purchase	\N	\N
3884	3884	299	1	2026-10-08	purchase	\N	\N
3885	3885	299	1	2026-10-08	purchase	\N	\N
3886	3886	299	1	2026-10-08	purchase	\N	\N
3887	3887	299	1	2026-10-08	donation	\N	\N
3888	3888	299	1	2026-10-08	purchase	\N	\N
3889	3889	299	1	2026-10-08	purchase	\N	\N
3890	3890	299	1	2026-10-08	purchase	\N	\N
3891	3891	299	1	2026-10-08	purchase	\N	\N
3892	3892	299	1	2026-10-08	purchase	\N	\N
3893	3893	299	1	2026-10-08	purchase	\N	\N
3894	3894	299	1	2026-10-08	donation	\N	\N
3895	3895	299	1	2026-10-08	purchase	\N	\N
3896	3896	299	1	2026-10-08	purchase	\N	\N
3897	3897	300	1	2026-10-08	purchase	\N	\N
3898	3898	300	1	2026-10-08	purchase	\N	\N
3899	3899	300	1	2026-10-08	donation	\N	\N
3900	3900	300	1	2026-10-08	purchase	\N	\N
3901	3901	300	1	2026-10-08	purchase	\N	\N
3902	3902	300	1	2026-10-08	purchase	\N	\N
3903	3903	300	1	2026-10-08	purchase	\N	\N
3904	3904	300	1	2026-10-08	purchase	\N	\N
3905	3905	300	1	2026-10-08	purchase	\N	\N
3906	3906	300	1	2026-10-08	donation	\N	\N
3907	3907	300	1	2026-10-08	purchase	\N	\N
3908	3908	301	1	2026-10-08	purchase	\N	\N
3909	3909	301	1	2026-10-08	donation	\N	\N
3910	3910	301	1	2026-10-08	purchase	\N	\N
3911	3911	301	1	2026-10-08	purchase	\N	\N
3912	3912	301	1	2026-10-08	purchase	\N	\N
3913	3913	301	1	2026-10-08	purchase	\N	\N
3914	3914	301	1	2026-10-08	purchase	\N	\N
3915	3915	301	1	2026-10-08	purchase	\N	\N
3916	3916	301	1	2026-10-08	donation	\N	\N
3917	3917	301	1	2026-10-08	purchase	\N	\N
3918	3918	301	1	2026-10-08	purchase	\N	\N
3919	3919	301	1	2026-10-08	purchase	\N	\N
3920	3920	301	1	2026-10-08	purchase	\N	\N
3921	3921	302	1	2026-10-08	donation	\N	\N
3922	3922	302	1	2026-10-08	purchase	\N	\N
3923	3923	302	1	2026-10-08	purchase	\N	\N
3924	3924	302	1	2026-10-08	purchase	\N	\N
3925	3925	302	1	2026-10-08	purchase	\N	\N
3926	3926	302	1	2026-10-08	purchase	\N	\N
3927	3927	302	1	2026-10-08	purchase	\N	\N
3928	3928	302	1	2026-10-08	donation	\N	\N
3929	3929	302	1	2026-10-08	purchase	\N	\N
3930	3930	303	1	2026-10-08	purchase	\N	\N
3931	3931	303	1	2026-10-08	purchase	\N	\N
3932	3932	303	1	2026-10-08	purchase	\N	\N
3933	3933	303	1	2026-10-08	purchase	\N	\N
3934	3934	303	1	2026-10-08	purchase	\N	\N
3935	3935	303	1	2026-10-08	purchase	\N	\N
3936	3936	303	1	2026-10-08	donation	\N	\N
3937	3937	303	1	2026-10-08	purchase	\N	\N
3938	3938	303	1	2026-10-08	purchase	\N	\N
3939	3939	303	1	2026-10-08	purchase	\N	\N
3940	3940	303	1	2026-10-08	purchase	\N	\N
3941	3941	303	1	2026-10-08	purchase	\N	\N
3942	3942	303	1	2026-10-08	purchase	\N	\N
3943	3943	303	1	2026-10-08	donation	\N	\N
3944	3944	303	1	2026-10-08	purchase	\N	\N
3945	3945	304	1	2026-10-08	purchase	\N	\N
3946	3946	304	1	2026-10-08	purchase	\N	\N
3947	3947	304	1	2026-10-08	purchase	\N	\N
3948	3948	304	1	2026-10-08	purchase	\N	\N
3949	3949	304	1	2026-10-08	purchase	\N	\N
3950	3950	304	1	2026-10-08	donation	\N	\N
3951	3951	304	1	2026-10-08	purchase	\N	\N
3952	3952	304	1	2026-10-08	purchase	\N	\N
3953	3953	304	1	2026-10-08	purchase	\N	\N
3954	3954	304	1	2026-10-08	purchase	\N	\N
3955	3955	304	1	2026-10-08	purchase	\N	\N
3956	3956	304	1	2026-10-08	purchase	\N	\N
3957	3957	304	1	2026-10-08	donation	\N	\N
3958	3958	305	1	2026-10-08	purchase	\N	\N
3959	3959	305	1	2026-10-08	purchase	\N	\N
3960	3960	305	1	2026-10-08	purchase	\N	\N
3961	3961	305	1	2026-10-08	purchase	\N	\N
3962	3962	305	1	2026-10-08	donation	\N	\N
3963	3963	305	1	2026-10-08	purchase	\N	\N
3964	3964	305	1	2026-10-08	purchase	\N	\N
3965	3965	305	1	2026-10-08	purchase	\N	\N
3966	3966	305	1	2026-10-08	purchase	\N	\N
3967	3967	305	1	2026-10-08	purchase	\N	\N
3968	3968	305	1	2026-10-08	purchase	\N	\N
3969	3969	306	1	2026-10-08	purchase	\N	\N
3970	3970	306	1	2026-10-08	purchase	\N	\N
3971	3971	306	1	2026-10-08	purchase	\N	\N
3972	3972	306	1	2026-10-08	donation	\N	\N
3973	3973	306	1	2026-10-08	purchase	\N	\N
3974	3974	306	1	2026-10-08	purchase	\N	\N
3975	3975	306	1	2026-10-08	purchase	\N	\N
3976	3976	306	1	2026-10-08	purchase	\N	\N
3977	3977	306	1	2026-10-08	purchase	\N	\N
3978	3978	306	1	2026-10-08	purchase	\N	\N
3979	3979	306	1	2026-10-08	donation	\N	\N
3980	3980	306	1	2026-10-08	purchase	\N	\N
3981	3981	306	1	2026-10-08	purchase	\N	\N
3982	3982	307	1	2026-10-08	purchase	\N	\N
3983	3983	307	1	2026-10-08	purchase	\N	\N
3984	3984	307	1	2026-10-08	donation	\N	\N
3985	3985	307	1	2026-10-08	purchase	\N	\N
3986	3986	307	1	2026-10-08	purchase	\N	\N
3987	3987	307	1	2026-10-08	purchase	\N	\N
3988	3988	307	1	2026-10-08	purchase	\N	\N
3989	3989	307	1	2026-10-08	purchase	\N	\N
3990	3990	307	1	2026-10-08	purchase	\N	\N
3991	3991	307	1	2026-10-08	donation	\N	\N
3992	3992	307	1	2026-10-08	purchase	\N	\N
3993	3993	307	1	2026-10-08	purchase	\N	\N
3994	3994	307	1	2026-10-08	purchase	\N	\N
3995	3995	307	1	2026-10-08	purchase	\N	\N
3996	3996	307	1	2026-10-08	purchase	\N	\N
3997	3997	308	1	2026-10-08	purchase	\N	\N
3998	3998	308	1	2026-10-08	donation	\N	\N
3999	3999	308	1	2026-10-08	purchase	\N	\N
4000	4000	308	1	2026-10-08	purchase	\N	\N
4001	4001	308	1	2026-10-08	purchase	\N	\N
4002	4002	308	1	2026-10-08	purchase	\N	\N
4003	4003	308	1	2026-10-08	purchase	\N	\N
4004	4004	308	1	2026-10-08	purchase	\N	\N
4005	4005	308	1	2026-10-08	donation	\N	\N
4006	4006	308	1	2026-10-08	purchase	\N	\N
4007	4007	308	1	2026-10-08	purchase	\N	\N
4008	4008	308	1	2026-10-08	purchase	\N	\N
4009	4009	308	1	2026-10-08	purchase	\N	\N
4010	4010	309	1	2026-10-08	donation	\N	\N
4011	4011	309	1	2026-10-08	purchase	\N	\N
4012	4012	309	1	2026-10-08	purchase	\N	\N
4013	4013	309	1	2026-10-08	purchase	\N	\N
4014	4014	309	1	2026-10-08	purchase	\N	\N
4015	4015	309	1	2026-10-08	purchase	\N	\N
4016	4016	309	1	2026-10-08	purchase	\N	\N
4017	4017	309	1	2026-10-08	donation	\N	\N
4018	4018	309	1	2026-10-08	purchase	\N	\N
4019	4019	309	1	2026-10-08	purchase	\N	\N
4020	4020	309	1	2026-10-08	purchase	\N	\N
4021	4021	310	1	2026-10-08	purchase	\N	\N
4022	4022	310	1	2026-10-08	purchase	\N	\N
4023	4023	310	1	2026-10-08	purchase	\N	\N
4024	4024	310	1	2026-10-08	purchase	\N	\N
4025	4025	310	1	2026-10-08	purchase	\N	\N
4026	4026	310	1	2026-10-08	purchase	\N	\N
4027	4027	310	1	2026-10-08	donation	\N	\N
4028	4028	310	1	2026-10-08	purchase	\N	\N
4029	4029	310	1	2026-10-08	purchase	\N	\N
4030	4030	310	1	2026-10-08	purchase	\N	\N
4031	4031	310	1	2026-10-08	purchase	\N	\N
4032	4032	311	1	2026-10-08	purchase	\N	\N
4033	4033	311	1	2026-10-08	purchase	\N	\N
4034	4034	311	1	2026-10-08	purchase	\N	\N
4035	4035	311	1	2026-10-08	purchase	\N	\N
4036	4036	311	1	2026-10-08	purchase	\N	\N
4037	4037	311	1	2026-10-08	donation	\N	\N
4038	4038	311	1	2026-10-08	purchase	\N	\N
4039	4039	311	1	2026-10-08	purchase	\N	\N
4040	4040	311	1	2026-10-08	purchase	\N	\N
4041	4041	311	1	2026-10-08	purchase	\N	\N
4042	4042	311	1	2026-10-08	purchase	\N	\N
4043	4043	311	1	2026-10-08	purchase	\N	\N
4044	4044	311	1	2026-10-08	donation	\N	\N
4045	4045	311	1	2026-10-08	purchase	\N	\N
4046	4046	311	1	2026-10-08	purchase	\N	\N
4047	4047	312	1	2026-10-08	purchase	\N	\N
4048	4048	312	1	2026-10-08	purchase	\N	\N
4049	4049	312	1	2026-10-08	purchase	\N	\N
4050	4050	312	1	2026-10-08	purchase	\N	\N
4051	4051	312	1	2026-10-08	donation	\N	\N
4052	4052	312	1	2026-10-08	purchase	\N	\N
4053	4053	312	1	2026-10-08	purchase	\N	\N
4054	4054	312	1	2026-10-08	purchase	\N	\N
4055	4055	312	1	2026-10-08	purchase	\N	\N
4056	4056	312	1	2026-10-08	purchase	\N	\N
4057	4057	312	1	2026-10-08	purchase	\N	\N
4058	4058	313	1	2026-10-08	purchase	\N	\N
4059	4059	313	1	2026-10-08	purchase	\N	\N
4060	4060	313	1	2026-10-08	purchase	\N	\N
4061	4061	313	1	2026-10-08	donation	\N	\N
4062	4062	313	1	2026-10-08	purchase	\N	\N
4063	4063	313	1	2026-10-08	purchase	\N	\N
4064	4064	313	1	2026-10-08	purchase	\N	\N
4065	4065	313	1	2026-10-08	purchase	\N	\N
4066	4066	313	1	2026-10-08	purchase	\N	\N
4067	4067	313	1	2026-10-08	purchase	\N	\N
4068	4068	313	1	2026-10-08	donation	\N	\N
4069	4069	313	1	2026-10-08	purchase	\N	\N
4070	4070	313	1	2026-10-08	purchase	\N	\N
4071	4071	314	1	2026-10-08	purchase	\N	\N
4072	4072	314	1	2026-10-08	purchase	\N	\N
4073	4073	314	1	2026-10-08	donation	\N	\N
4074	4074	314	1	2026-10-08	purchase	\N	\N
4075	4075	314	1	2026-10-08	purchase	\N	\N
4076	4076	314	1	2026-10-08	purchase	\N	\N
4077	4077	314	1	2026-10-08	purchase	\N	\N
4078	4078	314	1	2026-10-08	purchase	\N	\N
4079	4079	314	1	2026-10-08	purchase	\N	\N
4080	4080	314	1	2026-10-08	donation	\N	\N
4081	4081	314	1	2026-10-08	purchase	\N	\N
4082	4082	315	1	2026-10-08	purchase	\N	\N
4083	4083	315	1	2026-10-08	donation	\N	\N
4084	4084	315	1	2026-10-08	purchase	\N	\N
4085	4085	315	1	2026-10-08	purchase	\N	\N
4086	4086	315	1	2026-10-08	purchase	\N	\N
4087	4087	315	1	2026-10-08	purchase	\N	\N
4088	4088	315	1	2026-10-08	purchase	\N	\N
4089	4089	315	1	2026-10-08	purchase	\N	\N
4090	4090	315	1	2026-10-08	donation	\N	\N
4091	4091	315	1	2026-10-08	purchase	\N	\N
4092	4092	315	1	2026-10-08	purchase	\N	\N
4093	4093	316	1	2026-10-08	donation	\N	\N
4094	4094	316	1	2026-10-08	purchase	\N	\N
4095	4095	316	1	2026-10-08	purchase	\N	\N
4096	4096	316	1	2026-10-08	purchase	\N	\N
4097	4097	316	1	2026-10-08	purchase	\N	\N
4098	4098	316	1	2026-10-08	purchase	\N	\N
4099	4099	316	1	2026-10-08	purchase	\N	\N
4100	4100	316	1	2026-10-08	donation	\N	\N
4101	4101	316	1	2026-10-08	purchase	\N	\N
4102	4102	317	1	2026-10-08	purchase	\N	\N
4103	4103	317	1	2026-10-08	purchase	\N	\N
4104	4104	317	1	2026-10-08	purchase	\N	\N
4105	4105	317	1	2026-10-08	purchase	\N	\N
4106	4106	317	1	2026-10-08	purchase	\N	\N
4107	4107	317	1	2026-10-08	purchase	\N	\N
4108	4108	317	1	2026-10-08	donation	\N	\N
4109	4109	317	1	2026-10-08	purchase	\N	\N
4110	4110	317	1	2026-10-08	purchase	\N	\N
4111	4111	317	1	2026-10-08	purchase	\N	\N
4112	4112	317	1	2026-10-08	purchase	\N	\N
4113	4113	318	1	2026-10-08	purchase	\N	\N
4114	4114	318	1	2026-10-08	purchase	\N	\N
4115	4115	318	1	2026-10-08	purchase	\N	\N
4116	4116	318	1	2026-10-08	purchase	\N	\N
4117	4117	318	1	2026-10-08	purchase	\N	\N
4118	4118	318	1	2026-10-08	donation	\N	\N
4119	4119	318	1	2026-10-08	purchase	\N	\N
4120	4120	318	1	2026-10-08	purchase	\N	\N
4121	4121	318	1	2026-10-08	purchase	\N	\N
4122	4122	318	1	2026-10-08	purchase	\N	\N
4123	4123	318	1	2026-10-08	purchase	\N	\N
4124	4124	319	1	2026-10-08	purchase	\N	\N
4125	4125	319	1	2026-10-08	purchase	\N	\N
4126	4126	319	1	2026-10-08	purchase	\N	\N
4127	4127	319	1	2026-10-08	purchase	\N	\N
4128	4128	319	1	2026-10-08	donation	\N	\N
4129	4129	319	1	2026-10-08	purchase	\N	\N
4130	4130	319	1	2026-10-08	purchase	\N	\N
4131	4131	319	1	2026-10-08	purchase	\N	\N
4132	4132	319	1	2026-10-08	purchase	\N	\N
4133	4133	320	1	2026-10-08	purchase	\N	\N
4134	4134	320	1	2026-10-08	purchase	\N	\N
4135	4135	320	1	2026-10-08	purchase	\N	\N
4136	4136	320	1	2026-10-08	donation	\N	\N
4137	4137	320	1	2026-10-08	purchase	\N	\N
4138	4138	320	1	2026-10-08	purchase	\N	\N
4139	4139	320	1	2026-10-08	purchase	\N	\N
4140	4140	320	1	2026-10-08	purchase	\N	\N
4141	4141	320	1	2026-10-08	purchase	\N	\N
4142	4142	321	1	2026-10-08	purchase	\N	\N
4143	4143	321	1	2026-10-08	purchase	\N	\N
4144	4144	321	1	2026-10-08	donation	\N	\N
4145	4145	321	1	2026-10-08	purchase	\N	\N
4146	4146	321	1	2026-10-08	purchase	\N	\N
4147	4147	321	1	2026-10-08	purchase	\N	\N
4148	4148	321	1	2026-10-08	purchase	\N	\N
4149	4149	321	1	2026-10-08	purchase	\N	\N
4150	4150	321	1	2026-10-08	purchase	\N	\N
4151	4151	322	1	2026-10-08	purchase	\N	\N
4152	4152	322	1	2026-10-08	donation	\N	\N
4153	4153	322	1	2026-10-08	purchase	\N	\N
4154	4154	322	1	2026-10-08	purchase	\N	\N
4155	4155	322	1	2026-10-08	purchase	\N	\N
4156	4156	322	1	2026-10-08	purchase	\N	\N
4157	4157	322	1	2026-10-08	purchase	\N	\N
4158	4158	322	1	2026-10-08	purchase	\N	\N
4159	4159	322	1	2026-10-08	donation	\N	\N
4160	4160	322	1	2026-10-08	purchase	\N	\N
4161	4161	322	1	2026-10-08	purchase	\N	\N
4162	4162	323	1	2026-10-08	donation	\N	\N
4163	4163	323	1	2026-10-08	purchase	\N	\N
4164	4164	323	1	2026-10-08	purchase	\N	\N
4165	4165	323	1	2026-10-08	purchase	\N	\N
4166	4166	323	1	2026-10-08	purchase	\N	\N
4167	4167	323	1	2026-10-08	purchase	\N	\N
4168	4168	323	1	2026-10-08	purchase	\N	\N
4169	4169	323	1	2026-10-08	donation	\N	\N
4170	4170	324	1	2026-10-08	purchase	\N	\N
4171	4171	324	1	2026-10-08	purchase	\N	\N
4172	4172	324	1	2026-10-08	purchase	\N	\N
4173	4173	324	1	2026-10-08	purchase	\N	\N
4174	4174	324	1	2026-10-08	purchase	\N	\N
4175	4175	324	1	2026-10-08	purchase	\N	\N
4176	4176	324	1	2026-10-08	donation	\N	\N
4177	4177	324	1	2026-10-08	purchase	\N	\N
4178	4178	324	1	2026-10-08	purchase	\N	\N
4179	4179	325	1	2026-10-08	purchase	\N	\N
4180	4180	325	1	2026-10-08	purchase	\N	\N
4181	4181	325	1	2026-10-08	purchase	\N	\N
4182	4182	325	1	2026-10-08	purchase	\N	\N
4183	4183	325	1	2026-10-08	purchase	\N	\N
4184	4184	325	1	2026-10-08	donation	\N	\N
4185	4185	325	1	2026-10-08	purchase	\N	\N
4186	4186	325	1	2026-10-08	purchase	\N	\N
4187	4187	325	1	2026-10-08	purchase	\N	\N
4188	4188	326	1	2026-10-08	purchase	\N	\N
4189	4189	326	1	2026-10-08	purchase	\N	\N
4190	4190	326	1	2026-10-08	purchase	\N	\N
4191	4191	326	1	2026-10-08	purchase	\N	\N
4192	4192	326	1	2026-10-08	donation	\N	\N
4193	4193	326	1	2026-10-08	purchase	\N	\N
4194	4194	326	1	2026-10-08	purchase	\N	\N
4195	4195	326	1	2026-10-08	purchase	\N	\N
4196	4196	326	1	2026-10-08	purchase	\N	\N
4197	4197	327	1	2026-10-08	purchase	\N	\N
4198	4198	327	1	2026-10-08	purchase	\N	\N
4199	4199	327	1	2026-10-08	purchase	\N	\N
4200	4200	327	1	2026-10-08	donation	\N	\N
4201	4201	327	1	2026-10-08	purchase	\N	\N
4202	4202	327	1	2026-10-08	purchase	\N	\N
4203	4203	327	1	2026-10-08	purchase	\N	\N
4204	4204	327	1	2026-10-08	purchase	\N	\N
4205	4205	327	1	2026-10-08	purchase	\N	\N
4206	4206	327	1	2026-10-08	purchase	\N	\N
4207	4207	327	1	2026-10-08	donation	\N	\N
4208	4208	328	1	2026-10-08	purchase	\N	\N
4209	4209	328	1	2026-10-08	purchase	\N	\N
4210	4210	328	1	2026-10-08	donation	\N	\N
4211	4211	328	1	2026-10-08	purchase	\N	\N
4212	4212	328	1	2026-10-08	purchase	\N	\N
4213	4213	328	1	2026-10-08	purchase	\N	\N
4214	4214	328	1	2026-10-08	purchase	\N	\N
4215	4215	328	1	2026-10-08	purchase	\N	\N
4216	4216	328	1	2026-10-08	purchase	\N	\N
4217	4217	329	1	2026-10-08	purchase	\N	\N
4218	4218	329	1	2026-10-08	donation	\N	\N
4219	4219	329	1	2026-10-08	purchase	\N	\N
4220	4220	329	1	2026-10-08	purchase	\N	\N
4221	4221	329	1	2026-10-08	purchase	\N	\N
4222	4222	329	1	2026-10-08	purchase	\N	\N
4223	4223	329	1	2026-10-08	purchase	\N	\N
4224	4224	329	1	2026-10-08	purchase	\N	\N
4225	4225	330	1	2026-10-08	donation	\N	\N
4226	4226	330	1	2026-10-08	purchase	\N	\N
4227	4227	330	1	2026-10-08	purchase	\N	\N
4228	4228	330	1	2026-10-08	purchase	\N	\N
4229	4229	330	1	2026-10-08	purchase	\N	\N
4230	4230	330	1	2026-10-08	purchase	\N	\N
4231	4231	330	1	2026-10-08	purchase	\N	\N
4232	4232	331	1	2026-10-08	purchase	\N	\N
4233	4233	331	1	2026-10-08	purchase	\N	\N
4234	4234	331	1	2026-10-08	purchase	\N	\N
4235	4235	331	1	2026-10-08	purchase	\N	\N
4236	4236	331	1	2026-10-08	purchase	\N	\N
4237	4237	331	1	2026-10-08	purchase	\N	\N
4238	4238	331	1	2026-10-08	donation	\N	\N
4239	4239	331	1	2026-10-08	purchase	\N	\N
4240	4240	331	1	2026-10-08	purchase	\N	\N
4241	4241	331	1	2026-10-08	purchase	\N	\N
4242	4242	331	1	2026-10-08	purchase	\N	\N
4243	4243	331	1	2026-10-08	purchase	\N	\N
4244	4244	331	1	2026-10-08	purchase	\N	\N
4245	4245	331	1	2026-10-08	donation	\N	\N
4246	4246	331	1	2026-10-08	purchase	\N	\N
4247	4247	331	1	2026-10-08	purchase	\N	\N
4248	4248	331	1	2026-10-08	purchase	\N	\N
4249	4249	331	1	2026-10-08	purchase	\N	\N
4250	4250	331	1	2026-10-08	purchase	\N	\N
4251	4251	332	1	2026-10-08	purchase	\N	\N
4252	4252	333	1	2026-10-08	purchase	\N	\N
4253	4253	333	1	2026-10-08	purchase	\N	\N
4254	4254	333	1	2026-10-08	purchase	\N	\N
4255	4255	333	1	2026-10-08	purchase	\N	\N
4256	4256	333	1	2026-10-08	donation	\N	\N
4257	4257	333	1	2026-10-08	purchase	\N	\N
4258	4258	333	1	2026-10-08	purchase	\N	\N
4259	4259	333	1	2026-10-08	purchase	\N	\N
4260	4260	333	1	2026-10-08	purchase	\N	\N
4261	4261	333	1	2026-10-08	purchase	\N	\N
4262	4262	333	1	2026-10-08	purchase	\N	\N
4263	4263	333	1	2026-10-08	donation	\N	\N
4264	4264	333	1	2026-10-08	purchase	\N	\N
4265	4265	333	1	2026-10-08	purchase	\N	\N
4266	4266	333	1	2026-10-08	purchase	\N	\N
4267	4267	333	1	2026-10-08	purchase	\N	\N
4268	4268	333	1	2026-10-08	purchase	\N	\N
4269	4269	333	1	2026-10-08	purchase	\N	\N
4270	4270	333	1	2026-10-08	donation	\N	\N
4271	4271	333	1	2026-10-08	purchase	\N	\N
4272	4272	333	1	2026-10-08	purchase	\N	\N
4273	4273	334	1	2026-10-08	purchase	\N	\N
4274	4274	334	1	2026-10-08	purchase	\N	\N
4275	4275	334	1	2026-10-08	purchase	\N	\N
4276	4276	334	1	2026-10-08	donation	\N	\N
4277	4277	334	1	2026-10-08	purchase	\N	\N
4278	4278	334	1	2026-10-08	purchase	\N	\N
4279	4279	334	1	2026-10-08	purchase	\N	\N
4280	4280	334	1	2026-10-08	purchase	\N	\N
4281	4281	334	1	2026-10-08	purchase	\N	\N
4282	4282	334	1	2026-10-08	purchase	\N	\N
4283	4283	334	1	2026-10-08	donation	\N	\N
4284	4284	334	1	2026-10-08	purchase	\N	\N
4285	4285	334	1	2026-10-08	purchase	\N	\N
4286	4286	334	1	2026-10-08	purchase	\N	\N
4287	4287	334	1	2026-10-08	purchase	\N	\N
4288	4288	334	1	2026-10-08	purchase	\N	\N
4289	4289	334	1	2026-10-08	purchase	\N	\N
4290	4290	334	1	2026-10-08	donation	\N	\N
4291	4291	334	1	2026-10-08	purchase	\N	\N
4292	4292	335	1	2026-10-08	purchase	\N	\N
4293	4293	335	1	2026-10-08	purchase	\N	\N
4294	4294	335	1	2026-10-08	donation	\N	\N
4295	4295	335	1	2026-10-08	purchase	\N	\N
4296	4296	335	1	2026-10-08	purchase	\N	\N
4297	4297	335	1	2026-10-08	purchase	\N	\N
4298	4298	335	1	2026-10-08	purchase	\N	\N
4299	4299	335	1	2026-10-08	purchase	\N	\N
4300	4300	335	1	2026-10-08	purchase	\N	\N
4301	4301	335	1	2026-10-08	donation	\N	\N
4302	4302	335	1	2026-10-08	purchase	\N	\N
4303	4303	335	1	2026-10-08	purchase	\N	\N
4304	4304	335	1	2026-10-08	purchase	\N	\N
4305	4305	335	1	2026-10-08	purchase	\N	\N
4306	4306	335	1	2026-10-08	purchase	\N	\N
4307	4307	335	1	2026-10-08	purchase	\N	\N
4308	4308	335	1	2026-10-08	donation	\N	\N
4309	4309	335	1	2026-10-08	purchase	\N	\N
4310	4310	335	1	2026-10-08	purchase	\N	\N
4311	4311	335	1	2026-10-08	purchase	\N	\N
4312	4312	335	1	2026-10-08	purchase	\N	\N
4313	4313	336	1	2026-10-08	purchase	\N	\N
4314	4314	336	1	2026-10-08	donation	\N	\N
4315	4315	336	1	2026-10-08	purchase	\N	\N
4316	4316	336	1	2026-10-08	purchase	\N	\N
4317	4317	336	1	2026-10-08	purchase	\N	\N
4318	4318	336	1	2026-10-08	purchase	\N	\N
4319	4319	336	1	2026-10-08	purchase	\N	\N
4320	4320	336	1	2026-10-08	purchase	\N	\N
4321	4321	336	1	2026-10-08	donation	\N	\N
4322	4322	336	1	2026-10-08	purchase	\N	\N
4323	4323	336	1	2026-10-08	purchase	\N	\N
4324	4324	336	1	2026-10-08	purchase	\N	\N
4325	4325	336	1	2026-10-08	purchase	\N	\N
4326	4326	336	1	2026-10-08	purchase	\N	\N
4327	4327	336	1	2026-10-08	purchase	\N	\N
4328	4328	337	1	2026-10-08	donation	\N	\N
4329	4329	337	1	2026-10-08	purchase	\N	\N
4330	4330	337	1	2026-10-08	purchase	\N	\N
4331	4331	337	1	2026-10-08	purchase	\N	\N
4332	4332	337	1	2026-10-08	purchase	\N	\N
4333	4333	337	1	2026-10-08	purchase	\N	\N
4334	4334	337	1	2026-10-08	purchase	\N	\N
4335	4335	337	1	2026-10-08	donation	\N	\N
4336	4336	337	1	2026-10-08	purchase	\N	\N
4337	4337	337	1	2026-10-08	purchase	\N	\N
4338	4338	337	1	2026-10-08	purchase	\N	\N
4339	4339	337	1	2026-10-08	purchase	\N	\N
4340	4340	337	1	2026-10-08	purchase	\N	\N
4341	4341	337	1	2026-10-08	purchase	\N	\N
4342	4342	337	1	2026-10-08	donation	\N	\N
4343	4343	338	1	2026-10-08	purchase	\N	\N
4344	4344	338	1	2026-10-08	purchase	\N	\N
4345	4345	338	1	2026-10-08	purchase	\N	\N
4346	4346	338	1	2026-10-08	purchase	\N	\N
4347	4347	338	1	2026-10-08	purchase	\N	\N
4348	4348	338	1	2026-10-08	purchase	\N	\N
4349	4349	338	1	2026-10-08	donation	\N	\N
4350	4350	338	1	2026-10-08	purchase	\N	\N
4351	4351	338	1	2026-10-08	purchase	\N	\N
4352	4352	338	1	2026-10-08	purchase	\N	\N
4353	4353	338	1	2026-10-08	purchase	\N	\N
4354	4354	338	1	2026-10-08	purchase	\N	\N
4355	4355	338	1	2026-10-08	purchase	\N	\N
4356	4356	338	1	2026-10-08	donation	\N	\N
4357	4357	338	1	2026-10-08	purchase	\N	\N
4358	4358	339	1	2026-10-08	purchase	\N	\N
4359	4359	339	1	2026-10-08	purchase	\N	\N
4360	4360	339	1	2026-10-08	purchase	\N	\N
4361	4361	339	1	2026-10-08	purchase	\N	\N
4362	4362	339	1	2026-10-08	purchase	\N	\N
4363	4363	339	1	2026-10-08	donation	\N	\N
4364	4364	339	1	2026-10-08	purchase	\N	\N
4365	4365	339	1	2026-10-08	purchase	\N	\N
4366	4366	339	1	2026-10-08	purchase	\N	\N
4367	4367	339	1	2026-10-08	purchase	\N	\N
4368	4368	339	1	2026-10-08	purchase	\N	\N
4369	4369	340	1	2026-10-08	purchase	\N	\N
4370	4370	340	1	2026-10-08	purchase	\N	\N
4371	4371	340	1	2026-10-08	purchase	\N	\N
4372	4372	340	1	2026-10-08	purchase	\N	\N
4373	4373	340	1	2026-10-08	donation	\N	\N
4374	4374	340	1	2026-10-08	purchase	\N	\N
4375	4375	340	1	2026-10-08	purchase	\N	\N
4376	4376	340	1	2026-10-08	purchase	\N	\N
4377	4377	340	1	2026-10-08	purchase	\N	\N
4378	4378	340	1	2026-10-08	purchase	\N	\N
4379	4379	340	1	2026-10-08	purchase	\N	\N
4380	4380	340	1	2026-10-08	donation	\N	\N
4381	4381	340	1	2026-10-08	purchase	\N	\N
4382	4382	340	1	2026-10-08	purchase	\N	\N
4383	4383	340	1	2026-10-08	purchase	\N	\N
4384	4384	341	1	2026-10-08	purchase	\N	\N
4385	4385	341	1	2026-10-08	purchase	\N	\N
4386	4386	341	1	2026-10-08	purchase	\N	\N
4387	4387	341	1	2026-10-08	donation	\N	\N
4388	4388	341	1	2026-10-08	purchase	\N	\N
4389	4389	341	1	2026-10-08	purchase	\N	\N
4390	4390	341	1	2026-10-08	purchase	\N	\N
4391	4391	341	1	2026-10-08	purchase	\N	\N
4392	4392	341	1	2026-10-08	purchase	\N	\N
4393	4393	341	1	2026-10-08	purchase	\N	\N
4394	4394	341	1	2026-10-08	donation	\N	\N
4395	4395	342	1	2026-10-08	purchase	\N	\N
4396	4396	342	1	2026-10-08	purchase	\N	\N
4397	4397	342	1	2026-10-08	donation	\N	\N
4398	4398	342	1	2026-10-08	purchase	\N	\N
4399	4399	342	1	2026-10-08	purchase	\N	\N
4400	4400	342	1	2026-10-08	purchase	\N	\N
4401	4401	342	1	2026-10-08	purchase	\N	\N
4402	4402	342	1	2026-10-08	purchase	\N	\N
4403	4403	342	1	2026-10-08	purchase	\N	\N
4404	4404	342	1	2026-10-08	donation	\N	\N
4405	4405	342	1	2026-10-08	purchase	\N	\N
4406	4406	342	1	2026-10-08	purchase	\N	\N
4407	4407	342	1	2026-10-08	purchase	\N	\N
4408	4408	343	1	2026-10-08	purchase	\N	\N
4409	4409	343	1	2026-10-08	donation	\N	\N
4410	4410	343	1	2026-10-08	purchase	\N	\N
4411	4411	343	1	2026-10-08	purchase	\N	\N
4412	4412	343	1	2026-10-08	purchase	\N	\N
4413	4413	343	1	2026-10-08	purchase	\N	\N
4414	4414	343	1	2026-10-08	purchase	\N	\N
4415	4415	343	1	2026-10-08	purchase	\N	\N
4416	4416	343	1	2026-10-08	donation	\N	\N
4417	4417	344	1	2026-10-08	donation	\N	\N
4418	4418	344	1	2026-10-08	purchase	\N	\N
4419	4419	344	1	2026-10-08	purchase	\N	\N
4420	4420	344	1	2026-10-08	purchase	\N	\N
4421	4421	344	1	2026-10-08	purchase	\N	\N
4422	4422	344	1	2026-10-08	purchase	\N	\N
4423	4423	344	1	2026-10-08	purchase	\N	\N
4424	4424	344	1	2026-10-08	donation	\N	\N
4425	4425	344	1	2026-10-08	purchase	\N	\N
4426	4426	344	1	2026-10-08	purchase	\N	\N
4427	4427	344	1	2026-10-08	purchase	\N	\N
4428	4428	344	1	2026-10-08	purchase	\N	\N
4429	4429	344	1	2026-10-08	purchase	\N	\N
4430	4430	345	1	2026-10-08	purchase	\N	\N
4431	4431	345	1	2026-10-08	purchase	\N	\N
4432	4432	345	1	2026-10-08	purchase	\N	\N
4433	4433	345	1	2026-10-08	purchase	\N	\N
4434	4434	345	1	2026-10-08	purchase	\N	\N
4435	4435	345	1	2026-10-08	purchase	\N	\N
4436	4436	345	1	2026-10-08	donation	\N	\N
4437	4437	345	1	2026-10-08	purchase	\N	\N
4438	4438	345	1	2026-10-08	purchase	\N	\N
4439	4439	345	1	2026-10-08	purchase	\N	\N
4440	4440	345	1	2026-10-08	purchase	\N	\N
4441	4441	346	1	2026-10-08	purchase	\N	\N
4442	4442	346	1	2026-10-08	purchase	\N	\N
4443	4443	346	1	2026-10-08	purchase	\N	\N
4444	4444	346	1	2026-10-08	purchase	\N	\N
4445	4445	346	1	2026-10-08	purchase	\N	\N
4446	4446	346	1	2026-10-08	donation	\N	\N
4447	4447	346	1	2026-10-08	purchase	\N	\N
4448	4448	346	1	2026-10-08	purchase	\N	\N
4449	4449	346	1	2026-10-08	purchase	\N	\N
4450	4450	346	1	2026-10-08	purchase	\N	\N
4451	4451	346	1	2026-10-08	purchase	\N	\N
4452	4452	347	1	2026-10-08	purchase	\N	\N
4453	4453	347	1	2026-10-08	purchase	\N	\N
4454	4454	347	1	2026-10-08	purchase	\N	\N
4455	4455	347	1	2026-10-08	purchase	\N	\N
4456	4456	347	1	2026-10-08	donation	\N	\N
4457	4457	347	1	2026-10-08	purchase	\N	\N
4458	4458	347	1	2026-10-08	purchase	\N	\N
4459	4459	347	1	2026-10-08	purchase	\N	\N
4460	4460	347	1	2026-10-08	purchase	\N	\N
4461	4461	347	1	2026-10-08	purchase	\N	\N
4462	4462	347	1	2026-10-08	purchase	\N	\N
4463	4463	348	1	2026-10-08	purchase	\N	\N
4464	4464	348	1	2026-10-08	purchase	\N	\N
4465	4465	348	1	2026-10-08	purchase	\N	\N
4466	4466	348	1	2026-10-08	donation	\N	\N
4467	4467	348	1	2026-10-08	purchase	\N	\N
4468	4468	348	1	2026-10-08	purchase	\N	\N
4469	4469	348	1	2026-10-08	purchase	\N	\N
4470	4470	348	1	2026-10-08	purchase	\N	\N
4471	4471	348	1	2026-10-08	purchase	\N	\N
4472	4472	349	1	2026-10-08	purchase	\N	\N
4473	4473	349	1	2026-10-08	purchase	\N	\N
4474	4474	349	1	2026-10-08	donation	\N	\N
4475	4475	349	1	2026-10-08	purchase	\N	\N
4476	4476	349	1	2026-10-08	purchase	\N	\N
4477	4477	349	1	2026-10-08	purchase	\N	\N
4478	4478	349	1	2026-10-08	purchase	\N	\N
4479	4479	349	1	2026-10-08	purchase	\N	\N
4480	4480	349	1	2026-10-08	purchase	\N	\N
4481	4481	349	1	2026-10-08	donation	\N	\N
4482	4482	349	1	2026-10-08	purchase	\N	\N
4483	4483	350	1	2026-10-08	purchase	\N	\N
4484	4484	350	1	2026-10-08	donation	\N	\N
4485	4485	350	1	2026-10-08	purchase	\N	\N
4486	4486	350	1	2026-10-08	purchase	\N	\N
4487	4487	350	1	2026-10-08	purchase	\N	\N
4488	4488	350	1	2026-10-08	purchase	\N	\N
4489	4489	350	1	2026-10-08	purchase	\N	\N
4490	4490	350	1	2026-10-08	purchase	\N	\N
4491	4491	350	1	2026-10-08	donation	\N	\N
4492	4492	350	1	2026-10-08	purchase	\N	\N
4493	4493	350	1	2026-10-08	purchase	\N	\N
4494	4494	351	1	2026-10-08	donation	\N	\N
4495	4495	351	1	2026-10-08	purchase	\N	\N
4496	4496	351	1	2026-10-08	purchase	\N	\N
4497	4497	351	1	2026-10-08	purchase	\N	\N
4498	4498	351	1	2026-10-08	purchase	\N	\N
4499	4499	351	1	2026-10-08	purchase	\N	\N
4500	4500	351	1	2026-10-08	purchase	\N	\N
4501	4501	351	1	2026-10-08	donation	\N	\N
4502	4502	351	1	2026-10-08	purchase	\N	\N
4503	4503	352	1	2026-10-08	purchase	\N	\N
4504	4504	352	1	2026-10-08	purchase	\N	\N
4505	4505	352	1	2026-10-08	purchase	\N	\N
4506	4506	352	1	2026-10-08	purchase	\N	\N
4507	4507	352	1	2026-10-08	purchase	\N	\N
4508	4508	352	1	2026-10-08	purchase	\N	\N
4509	4509	352	1	2026-10-08	donation	\N	\N
4510	4510	352	1	2026-10-08	purchase	\N	\N
4511	4511	352	1	2026-10-08	purchase	\N	\N
4512	4512	352	1	2026-10-08	purchase	\N	\N
4513	4513	352	1	2026-10-08	purchase	\N	\N
4514	4514	352	1	2026-10-08	purchase	\N	\N
4515	4515	352	1	2026-10-08	purchase	\N	\N
4516	4516	353	1	2026-10-08	purchase	\N	\N
4517	4517	353	1	2026-10-08	purchase	\N	\N
4518	4518	353	1	2026-10-08	purchase	\N	\N
4519	4519	353	1	2026-10-08	purchase	\N	\N
4520	4520	353	1	2026-10-08	purchase	\N	\N
4521	4521	353	1	2026-10-08	donation	\N	\N
4522	4522	353	1	2026-10-08	purchase	\N	\N
4523	4523	353	1	2026-10-08	purchase	\N	\N
4524	4524	353	1	2026-10-08	purchase	\N	\N
4525	4525	353	1	2026-10-08	purchase	\N	\N
4526	4526	353	1	2026-10-08	purchase	\N	\N
4527	4527	354	1	2026-10-08	purchase	\N	\N
4528	4528	354	1	2026-10-08	purchase	\N	\N
4529	4529	354	1	2026-10-08	purchase	\N	\N
4530	4530	354	1	2026-10-08	purchase	\N	\N
4531	4531	354	1	2026-10-08	donation	\N	\N
4532	4532	354	1	2026-10-08	purchase	\N	\N
4533	4533	354	1	2026-10-08	purchase	\N	\N
4534	4534	354	1	2026-10-08	purchase	\N	\N
4535	4535	354	1	2026-10-08	purchase	\N	\N
4536	4536	354	1	2026-10-08	purchase	\N	\N
4537	4537	354	1	2026-10-08	purchase	\N	\N
4538	4538	355	1	2026-10-08	purchase	\N	\N
4539	4539	355	1	2026-10-08	purchase	\N	\N
4540	4540	355	1	2026-10-08	purchase	\N	\N
4541	4541	355	1	2026-10-08	donation	\N	\N
4542	4542	355	1	2026-10-08	purchase	\N	\N
4543	4543	355	1	2026-10-08	purchase	\N	\N
4544	4544	355	1	2026-10-08	purchase	\N	\N
4545	4545	355	1	2026-10-08	purchase	\N	\N
4546	4546	355	1	2026-10-08	purchase	\N	\N
4547	4547	356	1	2026-10-08	purchase	\N	\N
4548	4548	356	1	2026-10-08	purchase	\N	\N
4549	4549	356	1	2026-10-08	donation	\N	\N
4550	4550	356	1	2026-10-08	purchase	\N	\N
4551	4551	356	1	2026-10-08	purchase	\N	\N
4552	4552	356	1	2026-10-08	purchase	\N	\N
4553	4553	356	1	2026-10-08	purchase	\N	\N
4554	4554	356	1	2026-10-08	purchase	\N	\N
4555	4555	356	1	2026-10-08	purchase	\N	\N
4556	4556	356	1	2026-10-08	donation	\N	\N
4557	4557	356	1	2026-10-08	purchase	\N	\N
4558	4558	357	1	2026-10-08	purchase	\N	\N
4559	4559	357	1	2026-10-08	donation	\N	\N
4560	4560	357	1	2026-10-08	purchase	\N	\N
4561	4561	357	1	2026-10-08	purchase	\N	\N
4562	4562	357	1	2026-10-08	purchase	\N	\N
4563	4563	357	1	2026-10-08	purchase	\N	\N
4564	4564	357	1	2026-10-08	purchase	\N	\N
4565	4565	357	1	2026-10-08	purchase	\N	\N
4566	4566	357	1	2026-10-08	donation	\N	\N
4567	4567	358	1	2026-10-08	donation	\N	\N
4568	4568	358	1	2026-10-08	purchase	\N	\N
4569	4569	358	1	2026-10-08	purchase	\N	\N
4570	4570	358	1	2026-10-08	purchase	\N	\N
4571	4571	358	1	2026-10-08	purchase	\N	\N
4572	4572	358	1	2026-10-08	purchase	\N	\N
4573	4573	358	1	2026-10-08	purchase	\N	\N
4574	4574	358	1	2026-10-08	donation	\N	\N
4575	4575	358	1	2026-10-08	purchase	\N	\N
4576	4576	358	1	2026-10-08	purchase	\N	\N
4577	4577	358	1	2026-10-08	purchase	\N	\N
4578	4578	359	1	2026-10-08	purchase	\N	\N
4579	4579	359	1	2026-10-08	purchase	\N	\N
4580	4580	359	1	2026-10-08	purchase	\N	\N
4581	4581	359	1	2026-10-08	purchase	\N	\N
4582	4582	359	1	2026-10-08	purchase	\N	\N
4583	4583	359	1	2026-10-08	purchase	\N	\N
4584	4584	359	1	2026-10-08	donation	\N	\N
4585	4585	359	1	2026-10-08	purchase	\N	\N
4586	4586	359	1	2026-10-08	purchase	\N	\N
4587	4587	359	1	2026-10-08	purchase	\N	\N
4588	4588	359	1	2026-10-08	purchase	\N	\N
4589	4589	359	1	2026-10-08	purchase	\N	\N
4590	4590	359	1	2026-10-08	purchase	\N	\N
4591	4591	360	1	2026-10-08	purchase	\N	\N
4592	4592	360	1	2026-10-08	purchase	\N	\N
4593	4593	360	1	2026-10-08	purchase	\N	\N
4594	4594	360	1	2026-10-08	purchase	\N	\N
4595	4595	360	1	2026-10-08	purchase	\N	\N
4596	4596	360	1	2026-10-08	donation	\N	\N
4597	4597	360	1	2026-10-08	purchase	\N	\N
4598	4598	360	1	2026-10-08	purchase	\N	\N
4599	4599	360	1	2026-10-08	purchase	\N	\N
4600	4600	360	1	2026-10-08	purchase	\N	\N
4601	4601	360	1	2026-10-08	purchase	\N	\N
4602	4602	360	1	2026-10-08	purchase	\N	\N
4603	4603	360	1	2026-10-08	donation	\N	\N
4604	4604	361	1	2026-10-08	purchase	\N	\N
4605	4605	361	1	2026-10-08	purchase	\N	\N
4606	4606	361	1	2026-10-08	purchase	\N	\N
4607	4607	361	1	2026-10-08	purchase	\N	\N
4608	4608	361	1	2026-10-08	donation	\N	\N
4609	4609	361	1	2026-10-08	purchase	\N	\N
4610	4610	361	1	2026-10-08	purchase	\N	\N
4611	4611	361	1	2026-10-08	purchase	\N	\N
4612	4612	361	1	2026-10-08	purchase	\N	\N
4613	4613	361	1	2026-10-08	purchase	\N	\N
4614	4614	361	1	2026-10-08	purchase	\N	\N
4615	4615	362	1	2026-10-08	purchase	\N	\N
4616	4616	362	1	2026-10-08	purchase	\N	\N
4617	4617	362	1	2026-10-08	purchase	\N	\N
4618	4618	362	1	2026-10-08	donation	\N	\N
4619	4619	362	1	2026-10-08	purchase	\N	\N
4620	4620	362	1	2026-10-08	purchase	\N	\N
4621	4621	362	1	2026-10-08	purchase	\N	\N
4622	4622	362	1	2026-10-08	purchase	\N	\N
4623	4623	363	1	2026-10-08	purchase	\N	\N
4624	4624	363	1	2026-10-08	purchase	\N	\N
4625	4625	363	1	2026-10-08	donation	\N	\N
4626	4626	363	1	2026-10-08	purchase	\N	\N
4627	4627	363	1	2026-10-08	purchase	\N	\N
4628	4628	363	1	2026-10-08	purchase	\N	\N
4629	4629	363	1	2026-10-08	purchase	\N	\N
4630	4630	363	1	2026-10-08	purchase	\N	\N
4631	4631	363	1	2026-10-08	purchase	\N	\N
4632	4632	364	1	2026-10-08	purchase	\N	\N
4633	4633	364	1	2026-10-08	donation	\N	\N
4634	4634	364	1	2026-10-08	purchase	\N	\N
4635	4635	364	1	2026-10-08	purchase	\N	\N
4636	4636	364	1	2026-10-08	purchase	\N	\N
4637	4637	364	1	2026-10-08	purchase	\N	\N
4638	4638	364	1	2026-10-08	purchase	\N	\N
4639	4639	364	1	2026-10-08	purchase	\N	\N
4640	4640	364	1	2026-10-08	donation	\N	\N
4641	4641	365	1	2026-10-08	donation	\N	\N
4642	4642	365	1	2026-10-08	purchase	\N	\N
4643	4643	365	1	2026-10-08	purchase	\N	\N
4644	4644	365	1	2026-10-08	purchase	\N	\N
4645	4645	365	1	2026-10-08	purchase	\N	\N
4646	4646	365	1	2026-10-08	purchase	\N	\N
4647	4647	365	1	2026-10-08	purchase	\N	\N
4648	4648	365	1	2026-10-08	donation	\N	\N
4649	4649	365	1	2026-10-08	purchase	\N	\N
4650	4650	366	1	2026-10-08	purchase	\N	\N
4651	4651	366	1	2026-10-08	purchase	\N	\N
4652	4652	366	1	2026-10-08	purchase	\N	\N
4653	4653	366	1	2026-10-08	purchase	\N	\N
4654	4654	366	1	2026-10-08	purchase	\N	\N
4655	4655	366	1	2026-10-08	purchase	\N	\N
4656	4656	366	1	2026-10-08	donation	\N	\N
4657	4657	366	1	2026-10-08	purchase	\N	\N
4658	4658	366	1	2026-10-08	purchase	\N	\N
4659	4659	366	1	2026-10-08	purchase	\N	\N
4660	4660	366	1	2026-10-08	purchase	\N	\N
4661	4661	367	1	2026-10-08	purchase	\N	\N
4662	4662	367	1	2026-10-08	purchase	\N	\N
4663	4663	367	1	2026-10-08	purchase	\N	\N
4664	4664	367	1	2026-10-08	purchase	\N	\N
4665	4665	367	1	2026-10-08	purchase	\N	\N
4666	4666	367	1	2026-10-08	donation	\N	\N
4667	4667	367	1	2026-10-08	purchase	\N	\N
4668	4668	367	1	2026-10-08	purchase	\N	\N
4669	4669	368	1	2026-10-08	purchase	\N	\N
4670	4670	368	1	2026-10-08	purchase	\N	\N
4671	4671	368	1	2026-10-08	purchase	\N	\N
4672	4672	368	1	2026-10-08	purchase	\N	\N
4673	4673	368	1	2026-10-08	donation	\N	\N
4674	4674	368	1	2026-10-08	purchase	\N	\N
4675	4675	368	1	2026-10-08	purchase	\N	\N
4676	4676	368	1	2026-10-08	purchase	\N	\N
4677	4677	369	1	2026-10-08	purchase	\N	\N
4678	4678	369	1	2026-10-08	purchase	\N	\N
4679	4679	369	1	2026-10-08	purchase	\N	\N
4680	4680	369	1	2026-10-08	donation	\N	\N
4681	4681	369	1	2026-10-08	purchase	\N	\N
4682	4682	369	1	2026-10-08	purchase	\N	\N
4683	4683	369	1	2026-10-08	purchase	\N	\N
4684	4684	369	1	2026-10-08	purchase	\N	\N
4685	4685	369	1	2026-10-08	purchase	\N	\N
4686	4686	370	1	2026-10-08	purchase	\N	\N
4687	4687	370	1	2026-10-08	purchase	\N	\N
4688	4688	370	1	2026-10-08	donation	\N	\N
4689	4689	370	1	2026-10-08	purchase	\N	\N
4690	4690	370	1	2026-10-08	purchase	\N	\N
4691	4691	370	1	2026-10-08	purchase	\N	\N
4692	4692	370	1	2026-10-08	purchase	\N	\N
4693	4693	371	1	2026-10-08	purchase	\N	\N
4694	4694	372	1	2026-10-08	donation	\N	\N
4695	4695	372	1	2026-10-08	purchase	\N	\N
4696	4696	372	1	2026-10-08	purchase	\N	\N
4697	4697	372	1	2026-10-08	purchase	\N	\N
4698	4698	372	1	2026-10-08	purchase	\N	\N
4699	4699	372	1	2026-10-08	purchase	\N	\N
4700	4700	372	1	2026-10-08	purchase	\N	\N
4701	4701	372	1	2026-10-08	donation	\N	\N
4702	4702	372	1	2026-10-08	purchase	\N	\N
4703	4703	372	1	2026-10-08	purchase	\N	\N
4704	4704	372	1	2026-10-08	purchase	\N	\N
4705	4705	372	1	2026-10-08	purchase	\N	\N
4706	4706	372	1	2026-10-08	purchase	\N	\N
4707	4707	372	1	2026-10-08	purchase	\N	\N
4708	4708	372	1	2026-10-08	donation	\N	\N
4709	4709	372	1	2026-10-08	purchase	\N	\N
4710	4710	372	1	2026-10-08	purchase	\N	\N
4711	4711	372	1	2026-10-08	purchase	\N	\N
4712	4712	372	1	2026-10-08	purchase	\N	\N
4713	4713	372	1	2026-10-08	purchase	\N	\N
4714	4714	372	1	2026-10-08	purchase	\N	\N
4715	4715	373	1	2026-10-08	purchase	\N	\N
4716	4716	373	1	2026-10-08	purchase	\N	\N
4717	4717	373	1	2026-10-08	purchase	\N	\N
4718	4718	373	1	2026-10-08	purchase	\N	\N
4719	4719	373	1	2026-10-08	purchase	\N	\N
4720	4720	373	1	2026-10-08	purchase	\N	\N
4721	4721	373	1	2026-10-08	donation	\N	\N
4722	4722	373	1	2026-10-08	purchase	\N	\N
4723	4723	373	1	2026-10-08	purchase	\N	\N
4724	4724	373	1	2026-10-08	purchase	\N	\N
4725	4725	373	1	2026-10-08	purchase	\N	\N
4726	4726	373	1	2026-10-08	purchase	\N	\N
4727	4727	373	1	2026-10-08	purchase	\N	\N
4728	4728	373	1	2026-10-08	donation	\N	\N
4729	4729	373	1	2026-10-08	purchase	\N	\N
4730	4730	373	1	2026-10-08	purchase	\N	\N
4731	4731	373	1	2026-10-08	purchase	\N	\N
4732	4732	373	1	2026-10-08	purchase	\N	\N
4733	4733	373	1	2026-10-08	purchase	\N	\N
4734	4734	374	1	2026-10-08	purchase	\N	\N
4735	4735	374	1	2026-10-08	purchase	\N	\N
4736	4736	374	1	2026-10-08	purchase	\N	\N
4737	4737	374	1	2026-10-08	purchase	\N	\N
4738	4738	374	1	2026-10-08	purchase	\N	\N
4739	4739	374	1	2026-10-08	donation	\N	\N
4740	4740	374	1	2026-10-08	purchase	\N	\N
4741	4741	374	1	2026-10-08	purchase	\N	\N
4742	4742	374	1	2026-10-08	purchase	\N	\N
4743	4743	374	1	2026-10-08	purchase	\N	\N
4744	4744	374	1	2026-10-08	purchase	\N	\N
4745	4745	374	1	2026-10-08	purchase	\N	\N
4746	4746	374	1	2026-10-08	donation	\N	\N
4747	4747	374	1	2026-10-08	purchase	\N	\N
4748	4748	374	1	2026-10-08	purchase	\N	\N
4749	4749	374	1	2026-10-08	purchase	\N	\N
4750	4750	374	1	2026-10-08	purchase	\N	\N
4751	4751	374	1	2026-10-08	purchase	\N	\N
4752	4752	374	1	2026-10-08	purchase	\N	\N
4753	4753	375	1	2026-10-08	purchase	\N	\N
4754	4754	375	1	2026-10-08	purchase	\N	\N
4755	4755	375	1	2026-10-08	purchase	\N	\N
4756	4756	375	1	2026-10-08	purchase	\N	\N
4757	4757	375	1	2026-10-08	donation	\N	\N
4758	4758	375	1	2026-10-08	purchase	\N	\N
4759	4759	375	1	2026-10-08	purchase	\N	\N
4760	4760	375	1	2026-10-08	purchase	\N	\N
4761	4761	375	1	2026-10-08	purchase	\N	\N
4762	4762	375	1	2026-10-08	purchase	\N	\N
4763	4763	375	1	2026-10-08	purchase	\N	\N
4764	4764	375	1	2026-10-08	donation	\N	\N
4765	4765	375	1	2026-10-08	purchase	\N	\N
4766	4766	375	1	2026-10-08	purchase	\N	\N
4767	4767	375	1	2026-10-08	purchase	\N	\N
4768	4768	375	1	2026-10-08	purchase	\N	\N
4769	4769	375	1	2026-10-08	purchase	\N	\N
4770	4770	376	1	2026-10-08	purchase	\N	\N
4771	4771	376	1	2026-10-08	purchase	\N	\N
4772	4772	376	1	2026-10-08	purchase	\N	\N
4773	4773	376	1	2026-10-08	donation	\N	\N
4774	4774	376	1	2026-10-08	purchase	\N	\N
4775	4775	376	1	2026-10-08	purchase	\N	\N
4776	4776	376	1	2026-10-08	purchase	\N	\N
4777	4777	376	1	2026-10-08	purchase	\N	\N
4778	4778	376	1	2026-10-08	purchase	\N	\N
4779	4779	376	1	2026-10-08	purchase	\N	\N
4780	4780	376	1	2026-10-08	donation	\N	\N
4781	4781	376	1	2026-10-08	purchase	\N	\N
4782	4782	376	1	2026-10-08	purchase	\N	\N
4783	4783	376	1	2026-10-08	purchase	\N	\N
4784	4784	376	1	2026-10-08	purchase	\N	\N
4785	4785	377	1	2026-10-08	purchase	\N	\N
4786	4786	377	1	2026-10-08	purchase	\N	\N
4787	4787	377	1	2026-10-08	donation	\N	\N
4788	4788	377	1	2026-10-08	purchase	\N	\N
4789	4789	377	1	2026-10-08	purchase	\N	\N
4790	4790	377	1	2026-10-08	purchase	\N	\N
4791	4791	377	1	2026-10-08	purchase	\N	\N
4792	4792	377	1	2026-10-08	purchase	\N	\N
4793	4793	377	1	2026-10-08	purchase	\N	\N
4794	4794	377	1	2026-10-08	donation	\N	\N
4795	4795	377	1	2026-10-08	purchase	\N	\N
4796	4796	378	1	2026-10-08	purchase	\N	\N
4797	4797	378	1	2026-10-08	donation	\N	\N
4798	4798	378	1	2026-10-08	purchase	\N	\N
4799	4799	378	1	2026-10-08	purchase	\N	\N
4800	4800	378	1	2026-10-08	purchase	\N	\N
4801	4801	378	1	2026-10-08	purchase	\N	\N
4802	4802	378	1	2026-10-08	purchase	\N	\N
4803	4803	378	1	2026-10-08	purchase	\N	\N
4804	4804	378	1	2026-10-08	donation	\N	\N
4805	4805	378	1	2026-10-08	purchase	\N	\N
4806	4806	378	1	2026-10-08	purchase	\N	\N
4807	4807	379	1	2026-10-08	donation	\N	\N
4808	4808	379	1	2026-10-08	purchase	\N	\N
4809	4809	379	1	2026-10-08	purchase	\N	\N
4810	4810	379	1	2026-10-08	purchase	\N	\N
4811	4811	379	1	2026-10-08	purchase	\N	\N
4812	4812	379	1	2026-10-08	purchase	\N	\N
4813	4813	379	1	2026-10-08	purchase	\N	\N
4814	4814	379	1	2026-10-08	donation	\N	\N
4815	4815	379	1	2026-10-08	purchase	\N	\N
4816	4816	379	1	2026-10-08	purchase	\N	\N
4817	4817	379	1	2026-10-08	purchase	\N	\N
4818	4818	379	1	2026-10-08	purchase	\N	\N
4819	4819	379	1	2026-10-08	purchase	\N	\N
4820	4820	379	1	2026-10-08	purchase	\N	\N
4821	4821	379	1	2026-10-08	donation	\N	\N
4822	4822	380	1	2026-10-08	purchase	\N	\N
4823	4823	380	1	2026-10-08	purchase	\N	\N
4824	4824	380	1	2026-10-08	purchase	\N	\N
4825	4825	380	1	2026-10-08	purchase	\N	\N
4826	4826	380	1	2026-10-08	purchase	\N	\N
4827	4827	380	1	2026-10-08	purchase	\N	\N
4828	4828	380	1	2026-10-08	donation	\N	\N
4829	4829	380	1	2026-10-08	purchase	\N	\N
4830	4830	380	1	2026-10-08	purchase	\N	\N
4831	4831	380	1	2026-10-08	purchase	\N	\N
4832	4832	380	1	2026-10-08	purchase	\N	\N
4833	4833	381	1	2026-10-08	purchase	\N	\N
4834	4834	381	1	2026-10-08	purchase	\N	\N
4835	4835	381	1	2026-10-08	purchase	\N	\N
4836	4836	381	1	2026-10-08	purchase	\N	\N
4837	4837	381	1	2026-10-08	purchase	\N	\N
4838	4838	381	1	2026-10-08	donation	\N	\N
4839	4839	381	1	2026-10-08	purchase	\N	\N
4840	4840	381	1	2026-10-08	purchase	\N	\N
4841	4841	381	1	2026-10-08	purchase	\N	\N
4842	4842	381	1	2026-10-08	purchase	\N	\N
4843	4843	381	1	2026-10-08	purchase	\N	\N
4844	4844	382	1	2026-10-08	purchase	\N	\N
4845	4845	382	1	2026-10-08	purchase	\N	\N
4846	4846	382	1	2026-10-08	purchase	\N	\N
4847	4847	382	1	2026-10-08	purchase	\N	\N
4848	4848	382	1	2026-10-08	donation	\N	\N
4849	4849	382	1	2026-10-08	purchase	\N	\N
4850	4850	382	1	2026-10-08	purchase	\N	\N
4851	4851	382	1	2026-10-08	purchase	\N	\N
4852	4852	382	1	2026-10-08	purchase	\N	\N
4853	4853	383	1	2026-10-08	purchase	\N	\N
4854	4854	383	1	2026-10-08	purchase	\N	\N
4855	4855	383	1	2026-10-08	purchase	\N	\N
4856	4856	383	1	2026-10-08	donation	\N	\N
4857	4857	383	1	2026-10-08	purchase	\N	\N
4858	4858	383	1	2026-10-08	purchase	\N	\N
4859	4859	383	1	2026-10-08	purchase	\N	\N
4860	4860	383	1	2026-10-08	purchase	\N	\N
4861	4861	383	1	2026-10-08	purchase	\N	\N
4862	4862	383	1	2026-10-08	purchase	\N	\N
4863	4863	383	1	2026-10-08	donation	\N	\N
4864	4864	383	1	2026-10-08	purchase	\N	\N
4865	4865	383	1	2026-10-08	purchase	\N	\N
4866	4866	384	1	2026-10-08	purchase	\N	\N
4867	4867	384	1	2026-10-08	purchase	\N	\N
4868	4868	384	1	2026-10-08	donation	\N	\N
4869	4869	384	1	2026-10-08	purchase	\N	\N
4870	4870	384	1	2026-10-08	purchase	\N	\N
4871	4871	384	1	2026-10-08	purchase	\N	\N
4872	4872	384	1	2026-10-08	purchase	\N	\N
4873	4873	384	1	2026-10-08	purchase	\N	\N
4874	4874	384	1	2026-10-08	purchase	\N	\N
4875	4875	385	1	2026-10-08	purchase	\N	\N
4876	4876	385	1	2026-10-08	donation	\N	\N
4877	4877	385	1	2026-10-08	purchase	\N	\N
4878	4878	385	1	2026-10-08	purchase	\N	\N
4879	4879	385	1	2026-10-08	purchase	\N	\N
4880	4880	385	1	2026-10-08	purchase	\N	\N
4881	4881	385	1	2026-10-08	purchase	\N	\N
4882	4882	385	1	2026-10-08	purchase	\N	\N
4883	4883	385	1	2026-10-08	donation	\N	\N
4884	4884	385	1	2026-10-08	purchase	\N	\N
4885	4885	385	1	2026-10-08	purchase	\N	\N
4886	4886	386	1	2026-10-08	donation	\N	\N
4887	4887	386	1	2026-10-08	purchase	\N	\N
4888	4888	386	1	2026-10-08	purchase	\N	\N
4889	4889	386	1	2026-10-08	purchase	\N	\N
4890	4890	386	1	2026-10-08	purchase	\N	\N
4891	4891	386	1	2026-10-08	purchase	\N	\N
4892	4892	386	1	2026-10-08	purchase	\N	\N
4893	4893	386	1	2026-10-08	donation	\N	\N
4894	4894	386	1	2026-10-08	purchase	\N	\N
4895	4895	387	1	2026-10-08	purchase	\N	\N
4896	4896	387	1	2026-10-08	purchase	\N	\N
4897	4897	387	1	2026-10-08	purchase	\N	\N
4898	4898	387	1	2026-10-08	purchase	\N	\N
4899	4899	387	1	2026-10-08	purchase	\N	\N
4900	4900	387	1	2026-10-08	purchase	\N	\N
4901	4901	387	1	2026-10-08	donation	\N	\N
4902	4902	387	1	2026-10-08	purchase	\N	\N
4903	4903	387	1	2026-10-08	purchase	\N	\N
4904	4904	388	1	2026-10-08	purchase	\N	\N
4905	4905	388	1	2026-10-08	purchase	\N	\N
4906	4906	388	1	2026-10-08	purchase	\N	\N
4907	4907	388	1	2026-10-08	purchase	\N	\N
4908	4908	388	1	2026-10-08	purchase	\N	\N
4909	4909	388	1	2026-10-08	donation	\N	\N
4910	4910	388	1	2026-10-08	purchase	\N	\N
4911	4911	388	1	2026-10-08	purchase	\N	\N
4912	4912	388	1	2026-10-08	purchase	\N	\N
4913	4913	389	1	2026-10-08	purchase	\N	\N
4914	4914	389	1	2026-10-08	purchase	\N	\N
4915	4915	389	1	2026-10-08	purchase	\N	\N
4916	4916	389	1	2026-10-08	purchase	\N	\N
4917	4917	389	1	2026-10-08	donation	\N	\N
4918	4918	389	1	2026-10-08	purchase	\N	\N
4919	4919	389	1	2026-10-08	purchase	\N	\N
4920	4920	389	1	2026-10-08	purchase	\N	\N
4921	4921	389	1	2026-10-08	purchase	\N	\N
4922	4922	389	1	2026-10-08	purchase	\N	\N
4923	4923	389	1	2026-10-08	purchase	\N	\N
4924	4924	390	1	2026-10-08	purchase	\N	\N
4925	4925	390	1	2026-10-08	purchase	\N	\N
4926	4926	390	1	2026-10-08	purchase	\N	\N
4927	4927	390	1	2026-10-08	donation	\N	\N
4928	4928	390	1	2026-10-08	purchase	\N	\N
4929	4929	390	1	2026-10-08	purchase	\N	\N
4930	4930	390	1	2026-10-08	purchase	\N	\N
4931	4931	390	1	2026-10-08	purchase	\N	\N
4932	4932	390	1	2026-10-08	purchase	\N	\N
4933	4933	391	1	2026-10-08	purchase	\N	\N
4934	4934	391	1	2026-10-08	purchase	\N	\N
4935	4935	391	1	2026-10-08	donation	\N	\N
4936	4936	391	1	2026-10-08	purchase	\N	\N
4937	4937	391	1	2026-10-08	purchase	\N	\N
4938	4938	391	1	2026-10-08	purchase	\N	\N
4939	4939	391	1	2026-10-08	purchase	\N	\N
4940	4940	391	1	2026-10-08	purchase	\N	\N
4941	4941	391	1	2026-10-08	purchase	\N	\N
4942	4942	391	1	2026-10-08	donation	\N	\N
4943	4943	391	1	2026-10-08	purchase	\N	\N
4944	4944	391	1	2026-10-08	purchase	\N	\N
4945	4945	391	1	2026-10-08	purchase	\N	\N
4946	4946	392	1	2026-10-08	purchase	\N	\N
4947	4947	392	1	2026-10-08	donation	\N	\N
4948	4948	392	1	2026-10-08	purchase	\N	\N
4949	4949	392	1	2026-10-08	purchase	\N	\N
4950	4950	392	1	2026-10-08	purchase	\N	\N
4951	4951	392	1	2026-10-08	purchase	\N	\N
4952	4952	392	1	2026-10-08	purchase	\N	\N
4953	4953	392	1	2026-10-08	purchase	\N	\N
4954	4954	392	1	2026-10-08	donation	\N	\N
4955	4955	393	1	2026-10-08	donation	\N	\N
4956	4956	393	1	2026-10-08	purchase	\N	\N
4957	4957	393	1	2026-10-08	purchase	\N	\N
4958	4958	393	1	2026-10-08	purchase	\N	\N
4959	4959	393	1	2026-10-08	purchase	\N	\N
4960	4960	393	1	2026-10-08	purchase	\N	\N
4961	4961	393	1	2026-10-08	purchase	\N	\N
4962	4962	393	1	2026-10-08	donation	\N	\N
4963	4963	393	1	2026-10-08	purchase	\N	\N
4964	4964	393	1	2026-10-08	purchase	\N	\N
4965	4965	393	1	2026-10-08	purchase	\N	\N
4966	4966	394	1	2026-10-08	purchase	\N	\N
4967	4967	394	1	2026-10-08	purchase	\N	\N
4968	4968	394	1	2026-10-08	purchase	\N	\N
4969	4969	394	1	2026-10-08	purchase	\N	\N
4970	4970	394	1	2026-10-08	purchase	\N	\N
4971	4971	394	1	2026-10-08	purchase	\N	\N
4972	4972	394	1	2026-10-08	donation	\N	\N
4973	4973	394	1	2026-10-08	purchase	\N	\N
4974	4974	395	1	2026-10-08	purchase	\N	\N
4975	4975	395	1	2026-10-08	purchase	\N	\N
4976	4976	395	1	2026-10-08	purchase	\N	\N
4977	4977	395	1	2026-10-08	purchase	\N	\N
4978	4978	395	1	2026-10-08	purchase	\N	\N
4979	4979	395	1	2026-10-08	donation	\N	\N
4980	4980	395	1	2026-10-08	purchase	\N	\N
4981	4981	395	1	2026-10-08	purchase	\N	\N
4982	4982	395	1	2026-10-08	purchase	\N	\N
4983	4983	395	1	2026-10-08	purchase	\N	\N
4984	4984	395	1	2026-10-08	purchase	\N	\N
4985	4985	396	1	2026-10-08	purchase	\N	\N
4986	4986	396	1	2026-10-08	purchase	\N	\N
4987	4987	396	1	2026-10-08	purchase	\N	\N
4988	4988	396	1	2026-10-08	purchase	\N	\N
4989	4989	396	1	2026-10-08	donation	\N	\N
4990	4990	396	1	2026-10-08	purchase	\N	\N
4991	4991	396	1	2026-10-08	purchase	\N	\N
4992	4992	396	1	2026-10-08	purchase	\N	\N
4993	4993	396	1	2026-10-08	purchase	\N	\N
4994	4994	396	1	2026-10-08	purchase	\N	\N
4995	4995	396	1	2026-10-08	purchase	\N	\N
4996	4996	397	1	2026-10-08	purchase	\N	\N
4997	4997	397	1	2026-10-08	purchase	\N	\N
4998	4998	397	1	2026-10-08	purchase	\N	\N
4999	4999	397	1	2026-10-08	donation	\N	\N
5000	5000	397	1	2026-10-08	purchase	\N	\N
5001	5001	397	1	2026-10-08	purchase	\N	\N
5002	5002	397	1	2026-10-08	purchase	\N	\N
5003	5003	397	1	2026-10-08	purchase	\N	\N
5004	5004	397	1	2026-10-08	purchase	\N	\N
5005	5005	397	1	2026-10-08	purchase	\N	\N
5006	5006	397	1	2026-10-08	donation	\N	\N
5007	5007	397	1	2026-10-08	purchase	\N	\N
5008	5008	397	1	2026-10-08	purchase	\N	\N
5009	5009	398	1	2026-10-08	purchase	\N	\N
5010	5010	398	1	2026-10-08	purchase	\N	\N
5011	5011	398	1	2026-10-08	donation	\N	\N
5012	5012	398	1	2026-10-08	purchase	\N	\N
5013	5013	398	1	2026-10-08	purchase	\N	\N
5014	5014	398	1	2026-10-08	purchase	\N	\N
5015	5015	398	1	2026-10-08	purchase	\N	\N
5016	5016	398	1	2026-10-08	purchase	\N	\N
5017	5017	398	1	2026-10-08	purchase	\N	\N
5018	5018	398	1	2026-10-08	donation	\N	\N
5019	5019	398	1	2026-10-08	purchase	\N	\N
5020	5020	399	1	2026-10-08	purchase	\N	\N
5021	5021	399	1	2026-10-08	donation	\N	\N
5022	5022	399	1	2026-10-08	purchase	\N	\N
5023	5023	399	1	2026-10-08	purchase	\N	\N
5024	5024	399	1	2026-10-08	purchase	\N	\N
5025	5025	399	1	2026-10-08	purchase	\N	\N
5026	5026	399	1	2026-10-08	purchase	\N	\N
5027	5027	399	1	2026-10-08	purchase	\N	\N
5028	5028	400	1	2026-10-08	donation	\N	\N
5029	5029	400	1	2026-10-08	purchase	\N	\N
5030	5030	400	1	2026-10-08	purchase	\N	\N
5031	5031	400	1	2026-10-08	purchase	\N	\N
5032	5032	400	1	2026-10-08	purchase	\N	\N
5033	5033	400	1	2026-10-08	purchase	\N	\N
5034	5034	400	1	2026-10-08	purchase	\N	\N
5035	5035	400	1	2026-10-08	donation	\N	\N
5036	5036	401	1	2026-10-08	purchase	\N	\N
5037	5037	401	1	2026-10-08	purchase	\N	\N
5038	5038	401	1	2026-10-08	purchase	\N	\N
5039	5039	401	1	2026-10-08	purchase	\N	\N
5040	5040	401	1	2026-10-08	purchase	\N	\N
5041	5041	401	1	2026-10-08	purchase	\N	\N
5042	5042	401	1	2026-10-08	donation	\N	\N
5043	5043	401	1	2026-10-08	purchase	\N	\N
5044	5044	401	1	2026-10-08	purchase	\N	\N
5045	5045	402	1	2026-10-08	purchase	\N	\N
5046	5046	402	1	2026-10-08	purchase	\N	\N
5047	5047	402	1	2026-10-08	purchase	\N	\N
5048	5048	402	1	2026-10-08	purchase	\N	\N
5049	5049	402	1	2026-10-08	purchase	\N	\N
5050	5050	402	1	2026-10-08	donation	\N	\N
5051	5051	402	1	2026-10-08	purchase	\N	\N
5052	5052	403	1	2026-10-08	purchase	\N	\N
5053	5053	403	1	2026-10-08	purchase	\N	\N
5054	5054	403	1	2026-10-08	purchase	\N	\N
5055	5055	403	1	2026-10-08	purchase	\N	\N
5056	5056	403	1	2026-10-08	donation	\N	\N
5057	5057	403	1	2026-10-08	purchase	\N	\N
5058	5058	403	1	2026-10-08	purchase	\N	\N
5059	5059	403	1	2026-10-08	purchase	\N	\N
5060	5060	403	1	2026-10-08	purchase	\N	\N
5061	5061	404	1	2026-10-08	purchase	\N	\N
5062	5062	404	1	2026-10-08	purchase	\N	\N
5063	5063	404	1	2026-10-08	purchase	\N	\N
5064	5064	404	1	2026-10-08	donation	\N	\N
5065	5065	404	1	2026-10-08	purchase	\N	\N
5066	5066	404	1	2026-10-08	purchase	\N	\N
5067	5067	404	1	2026-10-08	purchase	\N	\N
5068	5068	405	1	2026-10-08	purchase	\N	\N
5069	5069	405	1	2026-10-08	purchase	\N	\N
5070	5070	405	1	2026-10-08	donation	\N	\N
5071	5071	405	1	2026-10-08	purchase	\N	\N
5072	5072	405	1	2026-10-08	purchase	\N	\N
5073	5073	405	1	2026-10-08	purchase	\N	\N
5074	5074	405	1	2026-10-08	purchase	\N	\N
5075	5075	405	1	2026-10-08	purchase	\N	\N
5076	5076	406	1	2026-10-08	purchase	\N	\N
5077	5077	406	1	2026-10-08	donation	\N	\N
5078	5078	406	1	2026-10-08	purchase	\N	\N
5079	5079	406	1	2026-10-08	purchase	\N	\N
5080	5080	406	1	2026-10-08	purchase	\N	\N
5081	5081	406	1	2026-10-08	purchase	\N	\N
5082	5082	406	1	2026-10-08	purchase	\N	\N
5083	5083	406	1	2026-10-08	purchase	\N	\N
5084	5084	407	1	2026-10-08	donation	\N	\N
5085	5085	407	1	2026-10-08	purchase	\N	\N
5086	5086	407	1	2026-10-08	purchase	\N	\N
5087	5087	407	1	2026-10-08	purchase	\N	\N
5088	5088	407	1	2026-10-08	purchase	\N	\N
5089	5089	407	1	2026-10-08	purchase	\N	\N
5090	5090	407	1	2026-10-08	purchase	\N	\N
5091	5091	408	1	2026-10-08	purchase	\N	\N
5092	5092	408	1	2026-10-08	purchase	\N	\N
5093	5093	408	1	2026-10-08	purchase	\N	\N
5094	5094	408	1	2026-10-08	purchase	\N	\N
5095	5095	408	1	2026-10-08	purchase	\N	\N
5096	5096	408	1	2026-10-08	purchase	\N	\N
5097	5097	408	1	2026-10-08	donation	\N	\N
5098	5098	408	1	2026-10-08	purchase	\N	\N
5099	5099	408	1	2026-10-08	purchase	\N	\N
5100	5100	409	1	2026-10-08	purchase	\N	\N
5101	900001	410	65	2026-10-12	purchase	\N	\N
5102	900002	411	65	2026-10-12	\N	\N	\N
5103	900010	412	65	2026-10-12	\N	\N	\N
5104	900020	413	65	2026-10-12	\N	\N	\N
\.


--
-- Data for Name: analytics_cache; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.analytics_cache (cache_id, report_type, filter_params, kpi_data, generated_by, generated_date) FROM stdin;
1	circulation_summary	{"end": "2026-12-31", "start": "2026-01-01", "departments": []}	{"usage": {"total": 102, "trend": [["2026-04-17", 1], ["2026-04-20", 1], ["2026-04-22", 1], ["2026-05-01", 1], ["2026-05-03", 2], ["2026-05-05", 1], ["2026-05-08", 1], ["2026-05-11", 1], ["2026-05-13", 1], ["2026-05-14", 1], ["2026-05-17", 1], ["2026-05-19", 1], ["2026-05-23", 1], ["2026-05-24", 2], ["2026-05-27", 1], ["2026-06-05", 1], ["2026-06-08", 2], ["2026-06-11", 1], ["2026-06-19", 1], ["2026-06-24", 1], ["2026-06-25", 1], ["2026-06-28", 1], ["2026-06-30", 2], ["2026-07-01", 1], ["2026-07-02", 1], ["2026-07-07", 1], ["2026-07-09", 1], ["2026-07-11", 1], ["2026-07-13", 2], ["2026-07-16", 1], ["2026-07-19", 1], ["2026-07-21", 1], ["2026-07-22", 1], ["2026-07-24", 2], ["2026-07-25", 1], ["2026-07-27", 1], ["2026-07-29", 1], ["2026-07-30", 1], ["2026-07-31", 1], ["2026-08-01", 1], ["2026-08-02", 1], ["2026-08-05", 1], ["2026-08-12", 2], ["2026-08-15", 1], ["2026-08-16", 1], ["2026-08-23", 1], ["2026-08-25", 2], ["2026-08-26", 1], ["2026-08-27", 1], ["2026-08-31", 1], ["2026-09-01", 1], ["2026-09-07", 1], ["2026-09-10", 2], ["2026-09-12", 1], ["2026-09-20", 1], ["2026-09-22", 3], ["2026-09-23", 2], ["2026-09-24", 1], ["2026-09-26", 1], ["2026-09-27", 1], ["2026-09-28", 1], ["2026-09-29", 2], ["2026-09-30", 1], ["2026-10-01", 3], ["2026-10-02", 3], ["2026-10-03", 4], ["2026-10-04", 2], ["2026-10-05", 1], ["2026-10-06", 3], ["2026-10-07", 2], ["2026-10-08", 3], ["2026-10-09", 1], ["2026-10-10", 1], ["2026-10-11", 1], ["2026-10-12", 2]], "recent": [["2026-10-12", "1347", "Demo Student One", "Student", "Calculus: Early Transcendentals", "James Stewart, Daniel K. Clegg, and Saleem Watson", "borrow", "2026-10-12 23:59:00", "returned"], ["2026-10-12", "0629", "Demo Student Two", "Student", "Podcasting: A Practical Guide", "Mia Lobel", "borrow", "2026-10-12 23:59:00", "active"], ["2026-10-11", "3176", "Rosa Aquino", "Student", "Understanding Public Administration", "Seung C. Lee and David H. Rosenbloom", "borrow", "2026-10-11 00:00:00", "active"], ["2026-10-10", "0004", "Maria Bautista", "Student", "McQuail's Mass Communication Theory", "Denis McQuail and Mark Deuze", "borrow", "2026-10-10 00:00:00", "returned"], ["2026-10-09", "0004", "Nina Bautista", "Faculty", "McQuail's Mass Communication Theory", "Denis McQuail and Mark Deuze", "borrow", "2026-11-08 00:00:00", "returned"], ["2026-10-08", "1621", "Carlos Mendoza", "Faculty", "Probability and Statistics", "Morris H. DeGroot and Mark J. Schervish", "borrow", "2026-10-08 00:00:00", "active"], ["2026-10-08", "1710", "John Mendoza", "Student", "Topology", "James R. Munkres", "borrow", "2026-10-10 00:00:00", "active"], ["2026-10-08", "3635", "Ella Aquino", "Faculty", "Statistics for Public Administration", "Evan M. Berman and Xiaohu Wang", "borrow", "2026-11-07 00:00:00", "returned"], ["2026-10-07", "0001", "Ana Aquino", "Student", "McQuail's Mass Communication Theory", "Denis McQuail and Mark Deuze", "borrow", "2026-10-07 00:00:00", "returned"], ["2026-10-07", "3410", "Carlos Mendoza", "Faculty", "Organization Theory and the Public Sector", "Tom Christensen, Per Laegreid, and Kjell Arne Rovik", "borrow", "2026-10-07 00:00:00", "returned"]], "overdue": 9, "top_books": [["McQuail's Mass Communication Theory", "Denis McQuail and Mark Deuze", 39], ["Foundations of Sport and Exercise Psychology", "Robert S. Weinberg and Daniel Gould", 2], ["Amusing Ourselves to Death", "Neil Postman", 2], ["Cybercrime Investigation", "John Bandler and Antonia Merzon", 2], ["Motor Learning and Performance", "Richard A. Schmidt and Timothy D. Lee", 1]], "department": "", "dept_total": 102, "departments": [], "return_rate": 73.5, "by_user_type": [["Student", 78], ["Faculty", 24]], "dept_summary": [["BEED", 17, 2, 1], ["BSIT", 17, 2, 1], ["BSBA", 17, 2, 2], ["BSED", 17, 2, 0], ["BSHM", 16, 2, 2], ["BS Criminology", 16, 2, 3], ["BSIS", 1, 1, 0], ["BSN", 1, 1, 0]], "by_department": [["BSED", 17], ["BEED", 17], ["BSIT", 17], ["BSBA", 17], ["BSHM", 16], ["BS Criminology", 16], ["BSIS", 1], ["BSN", 1]], "share_formula": "share = program borrowings / total borrowings x 100", "avg_per_borrower": 7.29, "trend_by_program": {"dates": ["2026-04-17", "2026-04-20", "2026-04-22", "2026-05-01", "2026-05-03", "2026-05-05", "2026-05-08", "2026-05-11", "2026-05-13", "2026-05-14", "2026-05-17", "2026-05-19", "2026-05-23", "2026-05-24", "2026-05-27", "2026-06-05", "2026-06-08", "2026-06-11", "2026-06-19", "2026-06-24", "2026-06-25", "2026-06-28", "2026-06-30", "2026-07-01", "2026-07-02", "2026-07-07", "2026-07-09", "2026-07-11", "2026-07-13", "2026-07-16", "2026-07-19", "2026-07-21", "2026-07-22", "2026-07-24", "2026-07-25", "2026-07-27", "2026-07-29", "2026-07-30", "2026-07-31", "2026-08-01", "2026-08-02", "2026-08-05", "2026-08-12", "2026-08-15", "2026-08-16", "2026-08-23", "2026-08-25", "2026-08-26", "2026-08-27", "2026-08-31", "2026-09-01", "2026-09-07", "2026-09-10", "2026-09-12", "2026-09-20", "2026-09-22", "2026-09-23", "2026-09-24", "2026-09-26", "2026-09-27", "2026-09-28", "2026-09-29", "2026-09-30", "2026-10-01", "2026-10-02", "2026-10-03", "2026-10-04", "2026-10-05", "2026-10-06", "2026-10-07", "2026-10-08", "2026-10-09", "2026-10-10", "2026-10-11", "2026-10-12"], "series": [{"total": 17, "values": [1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 1, 0, 0, 0, 1, 1, 0, 1, 0, 0, 0, 0], "program": "BSIT"}, {"total": 17, "values": [0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 1, 0, 0, 1, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 1, 1, 0, 0, 0, 0, 1, 0, 0, 0, 2, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0], "program": "BSED"}, {"total": 17, "values": [0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 1, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 1, 0, 0, 0], "program": "BEED"}, {"total": 17, "values": [0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 1, 0, 1, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 1, 1, 2, 1, 0, 0, 0, 0, 0, 1, 1, 0], "program": "BSBA"}, {"total": 16, "values": [0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 0, 0, 1, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0, 1, 1, 0, 0, 0, 0], "program": "BSHM"}, {"total": 16, "values": [0, 0, 0, 1, 0, 0, 1, 1, 0, 0, 0, 0, 1, 0, 0, 1, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 2, 0, 0, 0, 0, 1, 0, 0, 0, 0], "program": "BS Criminology"}]}, "unique_borrowers": 14, "by_department_all": [["BSED", 17], ["BEED", 17], ["BSIT", 17], ["BSBA", 17], ["BSHM", 16], ["BS Criminology", 16], ["BSIS", 1], ["BSN", 1]], "active_departments": 8, "overdue_by_program": {"dates": ["2026-05-07", "2026-05-11", "2026-05-13", "2026-05-14", "2026-05-26", "2026-06-10", "2026-07-16", "2026-08-03", "2026-10-04"], "series": [{"total": 3, "values": [0, 1, 0, 0, 0, 0, 1, 1, 0], "program": "BS Criminology"}, {"total": 2, "values": [0, 0, 1, 0, 0, 0, 0, 0, 1], "program": "BSBA"}, {"total": 2, "values": [0, 0, 0, 0, 1, 1, 0, 0, 0], "program": "BSHM"}, {"total": 1, "values": [1, 0, 0, 0, 0, 0, 0, 0, 0], "program": "BEED"}, {"total": 1, "values": [0, 0, 0, 1, 0, 0, 0, 0, 0], "program": "BSIT"}]}, "by_department_share": [["BSED", 17, 16.7], ["BEED", 17, 16.7], ["BSIT", 17, 16.7], ["BSBA", 17, 16.7], ["BSHM", 16, 15.7], ["BS Criminology", 16, 15.7], ["BSIS", 1, 1.0], ["BSN", 1, 1.0]], "top_books_by_program": [], "overdue_by_department": [["BS Criminology", 3], ["BSBA", 2], ["BSHM", 2], ["BEED", 1], ["BSIT", 1]], "borrowers_by_department": [["BEED", 2], ["BS Criminology", 2], ["BSBA", 2], ["BSED", 2], ["BSHM", 2], ["BSIT", 2], ["BSN", 1], ["BSIS", 1]], "by_department_share_all": [["BSED", 17, 16.7], ["BEED", 17, 16.7], ["BSIT", 17, 16.7], ["BSBA", 17, 16.7], ["BSHM", 16, 15.7], ["BS Criminology", 16, 15.7], ["BSIS", 1, 1.0], ["BSN", 1, 1.0]]}, "requests": {"total": 14, "trend": [["2026-10-12", 7]], "by_role": [["Philippine History: A New Narrative", 2, 1, 0, 3], ["Clean Architecture in Practice", 2, 0, 0, 2], ["Advanced Research Methods", 0, 1, 0, 1], ["Introduction to Data Science", 0, 1, 0, 1]], "pending": 7, "approved": 7, "procured": 0, "rejected": 0, "by_program": [["Nursing", 2], ["BSN", 2], ["BSIS", 1], ["Computing", 1], ["BACOMM", 1]], "top_titles": [["Philippine History: A New Narrative", 3], ["Clean Architecture in Practice", 2], ["Advanced Research Methods", 1], ["Introduction to Data Science", 1]]}, "collection": {"recent": [["900020", "Demo Capture Gamma", "Others", "missing", null, null, ""], ["900010", "Demo Capture Beta", "Others", "missing", null, null, ""], ["900002", "Demo Capture Alpha", "Others", "missing", null, null, ""], ["900001", "Dune", "Science Fiction", "available", null, null, ""], ["5099", "Universal Design for Learning", "Inclusive Education", "missing", null, null, ""], ["5098", "Universal Design for Learning", "Inclusive Education", "missing", null, null, ""], ["5097", "Universal Design for Learning", "Inclusive Education", "missing", null, null, ""], ["5096", "Universal Design for Learning", "Inclusive Education", "missing", null, null, ""], ["5095", "Universal Design for Learning", "Inclusive Education", "missing", null, null, ""], ["5094", "Universal Design for Learning", "Inclusive Education", "missing", null, null, ""]], "overdue": 9, "borrowed": 18, "reserved": 3, "available": 0, "condition": [["New / Excellent", 2], ["Very Good", 18], ["Good", 0], ["Fair", 5081], ["Poor", 5]], "cond_total": 5104, "by_category": [["Software Engineering", 7], ["Medical-Surgical Nursing", 6], ["Statistics", 5], ["Early Literacy", 5], ["Media Theory", 5], ["Inclusive Education", 5], ["Film Studies", 4], ["Dance", 4], ["Criminology", 4], ["Web Development", 4], ["Child Development", 4], ["Broadcast Journalism", 4], ["Public Administration Theory", 4], ["Programming", 4], ["New Media", 4], ["Forensic Science", 4], ["Abstract Algebra", 3], ["Autism", 3], ["Behavior Management", 3], ["Clinical Skills", 3], ["Community Health Nursing", 3], ["Corrections", 3], ["Criminal Investigation", 3], ["Data Science", 3], ["Deaf Education", 3], ["Discrete Mathematics", 3], ["History of Mathematics", 3], ["Human-Computer Interaction", 3], ["Information Security", 3], ["Information Systems", 3], ["Journalism", 3], ["Law Enforcement", 3], ["Learning Disabilities", 3], ["Mathematics Education", 3], ["Networking", 3], ["Nursing Education", 3], ["Nursing Ethics", 3], ["Operations Research", 3], ["Others", 3], ["Pharmacology", 3], ["Philippine Media", 3], ["Play", 3], ["Probability", 3], ["Project Management", 3], ["Public Finance", 3], ["Public Management", 3], ["Public Relations", 3], ["Real Analysis", 3], ["Speech Communication", 3], ["Team Sports", 3], ["Graph Theory", 2], ["Security Management", 2], ["Databases", 2], ["Differential Equations", 2], ["Disaster Management", 2], ["ADHD", 2], ["E-Governance", 2], ["Early Childhood Education", 2], ["Assessment", 2], ["Early Mathematics", 2], ["Emergency Nursing", 2], ["Exercise Physiology", 2], ["Family Partnerships", 2], ["First Aid", 2], ["Fitness", 2], ["Foundations", 2], ["Foundations of PE", 2], ["Fundamentals of Nursing", 2], ["Geometry", 2], ["Gifted Education", 2], ["Health Assessment", 2], ["Special Education", 2], ["Human Resource Management", 2], ["Visual Impairment", 2], ["Sport Psychology", 2], ["Intellectual Disability", 2], ["IT Governance", 2], ["Sports Management", 2], ["Juvenile Delinquency", 2], ["Language Development", 2], ["Sports Medicine", 2], ["Sports Nutrition", 2], ["Linear Algebra", 2], ["Local Governance", 2], ["Maternal and Child Nursing", 2], ["Media Criticism", 2], ["Media Law", 2], ["Anatomy and Physiology", 2], ["Media Writing", 2], ["Strength and Conditioning", 2], ["Number Theory", 2], ["Systems Analysis and Design", 2], ["Nursing Leadership", 2], ["Nursing Process", 2], ["Organization Theory", 2], ["PE Pedagogy", 2], ["Pediatric Nursing", 2], ["Therapy", 2], ["Philippine Politics", 2], ["Philippine Public Administration", 2], ["Advertising", 2], ["Administrative Law", 2], ["Public Ethics", 2], ["Urban Planning", 2], ["Public Policy", 2], ["Racket Sports", 2], ["Biomechanics", 2], ["Calculus", 2], ["Child Guidance", 2], ["Child Health and Nutrition", 2], ["Children's Literature", 2], ["Coaching", 2], ["Communication Research", 2], ["Comparative Administration", 2], ["Computer Architecture", 2], ["Research Methods", 2], ["Criminal Law", 2], ["Assistive Technology", 2], ["Cybercrime", 2], ["Criminal Justice", 1], ["Machine Learning", 1], ["Marksmanship", 1], ["Mass Communication", 1], ["Communication Theory", 1], ["Mathematical Modeling", 1], ["Mathematical Proof", 1], ["Adapted PE", 1], ["Victimology", 1], ["Media Ethics", 1], ["Media Industries", 1], ["Questioned Documents", 1], ["Media Literacy", 1], ["Recreation", 1], ["Critical Care Nursing", 1], ["Algorithms", 1], ["Microbiology", 1], ["Motor Development", 1], ["Motor Learning", 1], ["Music and Movement", 1], ["Board Review", 1], ["Algebra", 1], ["Nonprofit Management", 1], ["Biochemistry", 1], ["Numerical Analysis", 1], ["Complex Analysis", 1], ["Actuarial Science", 1], ["Nursing Informatics", 1], ["Athletics", 1], ["Criminal Procedure", 1], ["Nursing Research", 1], ["Assessment in PE", 1], ["Nursing Theory", 1], ["Nutrition", 1], ["Sensory Processing", 1], ["Development Administration", 1], ["Development Communication", 1], ["Operating Systems", 1], ["Terrorism", 1], ["Curriculum", 1], ["Diversity", 1], ["Drug Education", 1], ["Drug Enforcement", 1], ["E-Commerce", 1], ["Organizational Communication", 1], ["Early Childhood Curriculum", 1], ["Theory of Computing", 1], ["Early Intervention", 1], ["Outdoor Education", 1], ["Child Observation", 1], ["Early Science", 1], ["Child Protection", 1], ["Enterprise Architecture", 1], ["Evidence", 1], ["Perioperative Nursing", 1], ["Exercise Prescription", 1], ["Creative Arts", 1], ["Family Support", 1], ["Filipino Martial Arts", 1], ["Artificial Intelligence", 1], ["Financial Mathematics", 1], ["Philippine Criminal Justice", 1], ["Topology", 1], ["Forensic Ballistics", 1], ["Arson Investigation", 1], ["Civil Society", 1], ["Classroom Management", 1], ["Photojournalism", 1], ["Physical Disabilities", 1], ["Gerontologic Nursing", 1], ["Traffic Management", 1], ["Governance", 1], ["Dactyloscopy", 1], ["Policy Analysis", 1], ["Health Education", 1], ["Health Promotion", 1], ["Polygraphy", 1], ["Holistic Nursing", 1], ["Speech and Language", 1], ["Precalculus", 1], ["Human Rights", 1], ["IEP", 1], ["Aquatics", 1], ["Infant and Toddler Care", 1], ["Transcultural Nursing", 1], ["Problem Solving", 1], ["Procurement", 1], ["Intelligence", 1], ["Intercultural Communication", 1], ["Interpersonal Communication", 1], ["IT Ethics", 1], ["Visual Communication", 1], ["Transition", 1], ["Psychiatric Nursing", 1], ["Kinesiology", 1], ["Cloud Computing", 1], ["Science Fiction", 1], ["Trigonometry", 1], ["Public Leadership", 1]], "maintenance": 5078, "lost_damaged": 8, "total_copies": 5103, "total_titles": 412}, "circulation": {"total": 102, "trend": [["2026-04-17", 1], ["2026-04-20", 1], ["2026-04-22", 1], ["2026-05-01", 1], ["2026-05-03", 2], ["2026-05-05", 1], ["2026-05-08", 1], ["2026-05-11", 1], ["2026-05-13", 1], ["2026-05-14", 1], ["2026-05-17", 1], ["2026-05-19", 1], ["2026-05-23", 1], ["2026-05-24", 2], ["2026-05-27", 1], ["2026-06-05", 1], ["2026-06-08", 2], ["2026-06-11", 1], ["2026-06-19", 1], ["2026-06-24", 1], ["2026-06-25", 1], ["2026-06-28", 1], ["2026-06-30", 2], ["2026-07-01", 1], ["2026-07-02", 1], ["2026-07-07", 1], ["2026-07-09", 1], ["2026-07-11", 1], ["2026-07-13", 2], ["2026-07-16", 1], ["2026-07-19", 1], ["2026-07-21", 1], ["2026-07-22", 1], ["2026-07-24", 2], ["2026-07-25", 1], ["2026-07-27", 1], ["2026-07-29", 1], ["2026-07-30", 1], ["2026-07-31", 1], ["2026-08-01", 1], ["2026-08-02", 1], ["2026-08-05", 1], ["2026-08-12", 2], ["2026-08-15", 1], ["2026-08-16", 1], ["2026-08-23", 1], ["2026-08-25", 2], ["2026-08-26", 1], ["2026-08-27", 1], ["2026-08-31", 1], ["2026-09-01", 1], ["2026-09-07", 1], ["2026-09-10", 2], ["2026-09-12", 1], ["2026-09-20", 1], ["2026-09-22", 3], ["2026-09-23", 2], ["2026-09-24", 1], ["2026-09-26", 1], ["2026-09-27", 1], ["2026-09-28", 1], ["2026-09-29", 2], ["2026-09-30", 1], ["2026-10-01", 3], ["2026-10-02", 3], ["2026-10-03", 4], ["2026-10-04", 2], ["2026-10-05", 1], ["2026-10-06", 3], ["2026-10-07", 2], ["2026-10-08", 3], ["2026-10-09", 1], ["2026-10-10", 1], ["2026-10-11", 1], ["2026-10-12", 2]], "recent": [["2026-10-12", "1347", "Demo Student One", "Student", "Calculus: Early Transcendentals", "James Stewart, Daniel K. Clegg, and Saleem Watson", "borrow", "2026-10-12 23:59:00", "returned"], ["2026-10-12", "0629", "Demo Student Two", "Student", "Podcasting: A Practical Guide", "Mia Lobel", "borrow", "2026-10-12 23:59:00", "active"], ["2026-10-11", "3176", "Rosa Aquino", "Student", "Understanding Public Administration", "Seung C. Lee and David H. Rosenbloom", "borrow", "2026-10-11 00:00:00", "active"], ["2026-10-10", "0004", "Maria Bautista", "Student", "McQuail's Mass Communication Theory", "Denis McQuail and Mark Deuze", "borrow", "2026-10-10 00:00:00", "returned"], ["2026-10-09", "0004", "Nina Bautista", "Faculty", "McQuail's Mass Communication Theory", "Denis McQuail and Mark Deuze", "borrow", "2026-11-08 00:00:00", "returned"], ["2026-10-08", "1621", "Carlos Mendoza", "Faculty", "Probability and Statistics", "Morris H. DeGroot and Mark J. Schervish", "borrow", "2026-10-08 00:00:00", "active"], ["2026-10-08", "1710", "John Mendoza", "Student", "Topology", "James R. Munkres", "borrow", "2026-10-10 00:00:00", "active"], ["2026-10-08", "3635", "Ella Aquino", "Faculty", "Statistics for Public Administration", "Evan M. Berman and Xiaohu Wang", "borrow", "2026-11-07 00:00:00", "returned"], ["2026-10-07", "0001", "Ana Aquino", "Student", "McQuail's Mass Communication Theory", "Denis McQuail and Mark Deuze", "borrow", "2026-10-07 00:00:00", "returned"], ["2026-10-07", "3410", "Carlos Mendoza", "Faculty", "Organization Theory and the Public Sector", "Tom Christensen, Per Laegreid, and Kjell Arne Rovik", "borrow", "2026-10-07 00:00:00", "returned"]], "overdue": 9, "high_demand": [["McQuail's Mass Communication Theory", "Denis McQuail and Mark Deuze", 4], ["Fermat's Last Theorem", "Simon Singh", 1], ["Probability and Statistics", "Morris H. DeGroot and Mark J. Schervish", 1], ["Criminology: Theories, Patterns, and Typologies", "Larry J. Siegel", 1], ["Special Education: Contemporary Perspectives for School Professionals", "Marilyn Friend", 1]], "return_rate": 73.5, "avg_loan_days": 3.2, "fines_by_book": [["Introduction to Probability Models", "Sheldon M. Ross", 75.0, 1], ["Foundations of Sport and Exercise Psychology", "Robert S. Weinberg and Daniel Gould", 50.0, 1], ["McQuail's Mass Communication Theory", "Denis McQuail and Mark Deuze", 25.0, 1]], "new_additions": 412, "overdue_trend": [["2026-05-07", 1], ["2026-05-11", 1], ["2026-05-13", 1], ["2026-05-14", 1], ["2026-05-26", 1], ["2026-06-10", 1], ["2026-07-16", 1], ["2026-08-03", 1], ["2026-10-04", 1]], "top_categories": [["Media Theory", 39], ["Statistics", 2], ["Sport Psychology", 2], ["Probability", 2], ["Linear Algebra", 2], ["Film Studies", 2]], "active_borrowers": 14, "trend_by_program": {"dates": ["2026-04-17", "2026-04-20", "2026-04-22", "2026-05-01", "2026-05-03", "2026-05-05", "2026-05-08", "2026-05-11", "2026-05-13", "2026-05-14", "2026-05-17", "2026-05-19", "2026-05-23", "2026-05-24", "2026-05-27", "2026-06-05", "2026-06-08", "2026-06-11", "2026-06-19", "2026-06-24", "2026-06-25", "2026-06-28", "2026-06-30", "2026-07-01", "2026-07-02", "2026-07-07", "2026-07-09", "2026-07-11", "2026-07-13", "2026-07-16", "2026-07-19", "2026-07-21", "2026-07-22", "2026-07-24", "2026-07-25", "2026-07-27", "2026-07-29", "2026-07-30", "2026-07-31", "2026-08-01", "2026-08-02", "2026-08-05", "2026-08-12", "2026-08-15", "2026-08-16", "2026-08-23", "2026-08-25", "2026-08-26", "2026-08-27", "2026-08-31", "2026-09-01", "2026-09-07", "2026-09-10", "2026-09-12", "2026-09-20", "2026-09-22", "2026-09-23", "2026-09-24", "2026-09-26", "2026-09-27", "2026-09-28", "2026-09-29", "2026-09-30", "2026-10-01", "2026-10-02", "2026-10-03", "2026-10-04", "2026-10-05", "2026-10-06", "2026-10-07", "2026-10-08", "2026-10-09", "2026-10-10", "2026-10-11", "2026-10-12"], "series": [{"total": 17, "values": [1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 1, 0, 0, 0, 1, 1, 0, 1, 0, 0, 0, 0], "program": "BSIT"}, {"total": 17, "values": [0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 1, 0, 0, 1, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 1, 1, 0, 0, 0, 0, 1, 0, 0, 0, 2, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0], "program": "BSED"}, {"total": 17, "values": [0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 1, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 1, 0, 0, 0], "program": "BEED"}, {"total": 17, "values": [0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 1, 0, 1, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 1, 1, 2, 1, 0, 0, 0, 0, 0, 1, 1, 0], "program": "BSBA"}, {"total": 16, "values": [0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 0, 0, 1, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0, 1, 1, 0, 0, 0, 0], "program": "BSHM"}, {"total": 16, "values": [0, 0, 0, 1, 0, 0, 1, 1, 0, 0, 0, 0, 1, 0, 0, 1, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 2, 0, 0, 0, 0, 1, 0, 0, 0, 0], "program": "BS Criminology"}]}, "overdue_by_program": {"dates": ["2026-05-07", "2026-05-11", "2026-05-13", "2026-05-14", "2026-05-26", "2026-06-10", "2026-07-16", "2026-08-03", "2026-10-04"], "series": [{"total": 3, "values": [0, 1, 0, 0, 0, 0, 1, 1, 0], "program": "BS Criminology"}, {"total": 2, "values": [0, 0, 1, 0, 0, 0, 0, 0, 1], "program": "BSBA"}, {"total": 2, "values": [0, 0, 0, 0, 1, 1, 0, 0, 0], "program": "BSHM"}, {"total": 1, "values": [1, 0, 0, 0, 0, 0, 0, 0, 0], "program": "BEED"}, {"total": 1, "values": [0, 0, 0, 1, 0, 0, 0, 0, 0], "program": "BSIT"}]}, "top_books_by_program": [], "top_categories_by_program": []}}	65	2026-10-12 21:59:32.219002
2	books_borrowed_per_program	{"to": "", "from": "", "preset": "all", "department": []}	[["BSED", 17], ["BEED", 17], ["BSIT", 17], ["BSBA", 17], ["BSHM", 16], ["BS Criminology", 16], ["BSIS", 1], ["BSN", 1]]	65	2026-10-12 21:59:32.332635
3	utilization_rate	{"to": "", "from": "", "preset": "all", "department": []}	3.88	65	2026-10-12 21:59:32.334438
4	most_borrowed_titles	{"to": "", "from": "", "preset": "all", "department": []}	[["McQuail's Mass Communication Theory", 39], ["Foundations of Sport and Exercise Psychology", 2], ["Amusing Ourselves to Death", 2], ["Cybercrime Investigation", 2], ["Adapted Physical Education and Sport", 1], ["The City Reader", 1], ["Motor Learning and Performance", 1], ["Calculus: Early Transcendentals", 1], ["Fingerprint Identification", 1], ["Test Success: Test-Taking Techniques for Beginning Nursing Students", 1]]	65	2026-10-12 21:59:32.336102
5	underutilized_titles	{"to": "", "from": "", "preset": "all", "department": []}	[[" Managing Public Sector Projects"], ["A First Course in Abstract Algebra"], ["A First Course in Probability"], ["A Guide to the Project Management Body of Knowledge (PMBOK Guide)"], ["A Parent's Guide to High-Functioning Autism"], ["Abstract Algebra"], ["Accounting Information Systems"], ["ACSM's Guidelines for Exercise Testing and Prescription"], ["Administrative Law"], ["Administrative Reforms in Asia"]]	65	2026-10-12 21:59:32.338025
\.


--
-- Data for Name: audit_trail; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.audit_trail (log_id, user_id, activity, session_token, log_timestamp) FROM stdin;
5	1	settings:update:10:MAX_BORROW_LIMIT_STUDENT,MAX_BORROW_LIMIT_FACULTY,OVERNIGHT_DUE_DAYS_STUDENT,OVERNIGHT_DUE_DAYS_FACULTY,DAILY_CIRCULATION_DUE_DAYS,OVERDUE_FINE_PER_DAY,OVERDUE_GRACE_DAYS,RESERVATION_CLAIM_DAYS,RESERVATION_CLAIM_HOURS,DUE_SOON_NOTIFY_DA	\N	2026-10-08 01:12:16.061204
6	1	settings:update:12:MAX_BORROW_LIMIT_STUDENT,MAX_BORROW_LIMIT_FACULTY,OVERNIGHT_DUE_DAYS_STUDENT,OVERNIGHT_DUE_DAYS_FACULTY,DAILY_CIRCULATION_DUE_DAYS,OVERDUE_FINE_PER_DAY,OVERDUE_GRACE_DAYS,RESERVATION_CLAIM_DAYS,RESERVATION_CLAIM_HOURS,DUE_SOON_NOTIFY_DA	\N	2026-10-08 01:12:58.194444
7	1	circulation:borrow:3497	\N	2026-10-08 01:37:35.12785
12	1	[SEEDSUP] login	\N	2026-10-12 21:55:43.29135
13	1	[SEEDSUP] cataloging:export_books:all:10	\N	2026-10-12 21:55:43.29135
14	60	[SEEDSUP] login	\N	2026-10-12 21:55:43.29135
15	60	[SEEDSUP] cataloging:export_books:all:10	\N	2026-10-12 21:55:43.29135
16	60	security:denied:main.librarian_dashboard	\N	2026-10-12 21:56:37.933143
17	\N	system:auth_required:/librarian	\N	2026-10-12 21:56:56.698301
18	\N	system:auth_required:/librarian	\N	2026-10-12 21:56:56.702945
19	\N	system:auth_required:/user/profile	\N	2026-10-12 21:56:56.704721
20	60	security:denied:main.librarian_dashboard	\N	2026-10-12 21:57:57.273426
21	60	requests:create:40	\N	2026-10-12 21:59:21.381599
22	65	requests:approve:40	\N	2026-10-12 21:59:21.485472
23	65	procurement:update_status:19	\N	2026-10-12 21:59:21.497807
24	65	cataloging:add_book	\N	2026-10-12 21:59:21.598172
25	65	cataloging:bulk_import:3_success_0_errors	\N	2026-10-12 21:59:21.917637
26	65	circulation:borrow:629	\N	2026-10-12 21:59:23.98661
27	60	circulation:user_reserve:50	\N	2026-10-12 21:59:24.084719
28	60	circulation:user_borrow:101	\N	2026-10-12 21:59:24.180757
29	65	circulation:return:323	\N	2026-10-12 21:59:24.309566
30	65	inventory:start_session:3	\N	2026-10-12 21:59:24.331585
31	65	inventory:scan:5101	\N	2026-10-12 21:59:24.347108
32	65	inventory:scan:1347	\N	2026-10-12 21:59:24.443746
33	65	inventory:complete_session:3	\N	2026-10-12 21:59:32.145178
34	60	profile:update	\N	2026-10-12 21:59:32.402284
\.


--
-- Data for Name: backup_log; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.backup_log (backup_id, filename, size_bytes, status, backup_type, error_msg, created_at) FROM stdin;
1	library_backup_20261012_215932_in_progress.sql	\N	in_progress	manual	\N	2026-10-12 21:59:32.731927
\.


--
-- Data for Name: book_catalog; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.book_catalog (book_id, title, author, edition, publisher, year_published, subject_classification, call_number, isbn, material_type, description, catalog_status, date_added, updated_at, updated_by) FROM stdin;
1	McQuail's Mass Communication Theory	Denis McQuail and Mark Deuze	7th	SAGE Publications	2020	Media Theory	P90.A100 2020	978-1-000-00000-9	Book	Foundational theory of mass communication and media effects. Recommended for Bachelor of Arts in Communication.	active	2026-10-08	\N	\N
2	Understanding Media: The Extensions of Man	Marshall McLuhan	Reprint	MIT Press	1994	Media Theory	P90.B137 1994	978-1-000-07919-7	Book	Classic study of media as extensions of human senses. Recommended for Bachelor of Arts in Communication.	active	2026-10-08	\N	\N
3	Mass Communication: Living in a Media World	Ralph E. Hanson	8th	SAGE Publications	2021	Mass Communication	P90.C174 2021	978-1-000-15838-0	Book	Introductory survey of mass media industries and issues. Recommended for Bachelor of Arts in Communication.	active	2026-10-08	\N	\N
4	Media Literacy	W. James Potter	10th	SAGE Publications	2021	Media Literacy	P90.D211 2021	978-1-000-23757-3	Book	Framework for critically analyzing media messages. Recommended for Bachelor of Arts in Communication.	active	2026-10-08	\N	\N
5	The Elements of Journalism	Bill Kovach and Tom Rosenstiel	4th	Crown	2021	Journalism	P90.E248 2021	978-1-000-31676-6	Book	Core principles and purpose of journalism. Recommended for Bachelor of Arts in Communication.	active	2026-10-08	\N	\N
6	Writing for the Mass Media	James G. Stovall	10th	Pearson	2018	Media Writing	P90.F285 2018	978-1-000-39595-2	Book	Practical guide to news, PR, and broadcast writing. Recommended for Bachelor of Arts in Communication.	active	2026-10-08	\N	\N
7	The Associated Press Stylebook	Associated Press	57th	Basic Books	2024	Journalism	P90.G322 2024	978-1-000-47514-2	Book	Standard style and usage guide for journalists. Recommended for Bachelor of Arts in Communication.	active	2026-10-08	\N	\N
8	Public Relations: Strategies and Tactics	Dennis L. Wilcox and Glen T. Cameron	12th	Pearson	2020	Public Relations	P90.H359 2020	978-1-000-55433-5	Book	Comprehensive introduction to PR planning and practice. Recommended for Bachelor of Arts in Communication.	active	2026-10-08	\N	\N
9	Advertising: Principles and Practice	Sandra Moriarty, Nancy Mitchell, and William Wells	11th	Pearson	2021	Advertising	P90.I396 2021	978-1-000-63352-8	Book	Principles of advertising strategy and creative execution. Recommended for Bachelor of Arts in Communication.	active	2026-10-08	\N	\N
10	Broadcast News Writing, Style, and Reporting	Ted White and Frank Barnas	5th	Routledge	2012	Broadcast Journalism	P90.J433 2012	978-1-000-71271-1	Book	Writing and producing news for radio and television. Recommended for Bachelor of Arts in Communication.	active	2026-10-08	\N	\N
11	Media Ethics: Cases and Moral Reasoning	Clifford G. Christians, Mark Fackler, and Kathy Brittain Richardson	11th	Routledge	2020	Media Ethics	P90.K470 2020	978-1-000-79190-7	Book	Case-based approach to ethical decision-making in media. Recommended for Bachelor of Arts in Communication.	active	2026-10-08	\N	\N
12	An Introduction to Visual Communication	Susan Barnes	3rd	Peter Lang	2017	Visual Communication	P90.L507 2017	978-1-000-87109-8	Book	How images communicate meaning across media. Recommended for Bachelor of Arts in Communication.	active	2026-10-08	\N	\N
13	Film Art: An Introduction	David Bordwell, Kristin Thompson, and Jeff Smith	13th	McGraw-Hill	2023	Film Studies	P90.M544 2023	978-1-000-95028-1	Book	Formal analysis of film style and narration. Recommended for Bachelor of Arts in Communication.	active	2026-10-08	\N	\N
14	Convergence Culture	Henry Jenkins	Reprint	NYU Press	2008	New Media	P90.N581 2008	978-1-001-02947-4	Book	Where old and new media collide in participatory culture. Recommended for Bachelor of Arts in Communication.	active	2026-10-08	\N	\N
15	The Medium Is the Massage	Marshall McLuhan and Quentin Fiore	Reprint	Gingko Press	2001	Media Theory	P90.O618 2001	978-1-001-10866-7	Book	Illustrated exploration of media effects. Recommended for Bachelor of Arts in Communication.	active	2026-10-08	\N	\N
16	Manufacturing Consent	Edward S. Herman and Noam Chomsky	Reprint	Pantheon	2002	Media Criticism	P90.P655 2002	978-1-001-18785-3	Book	Propaganda model of mass media in democracies. Recommended for Bachelor of Arts in Communication.	active	2026-10-08	\N	\N
17	Amusing Ourselves to Death	Neil Postman	Reprint	Penguin	2005	Media Criticism	P90.Q692 2005	978-1-001-26704-3	Book	Public discourse in the age of show business. Recommended for Bachelor of Arts in Communication.	active	2026-10-08	\N	\N
18	Public Opinion	Walter Lippmann	Reprint	Free Press	1997	Media Theory	P90.R729 1997	978-1-001-34623-6	Book	Classic on public opinion and the press. Recommended for Bachelor of Arts in Communication.	active	2026-10-08	\N	\N
19	Theories of Human Communication	Stephen W. Littlejohn, Karen A. Foss, and John G. Oetzel	12th	Waveland Press	2021	Communication Theory	P90.S766 2021	978-1-001-42542-9	Book	Survey of major human communication theories. Recommended for Bachelor of Arts in Communication.	active	2026-10-08	\N	\N
20	Interpersonal Communication: Everyday Encounters	Julia T. Wood	9th	Cengage	2019	Interpersonal Communication	P90.T803 2019	978-1-001-50461-2	Book	Applying interpersonal theory to daily interaction. Recommended for Bachelor of Arts in Communication.	active	2026-10-08	\N	\N
21	Organizational Communication: Approaches and Processes	Katherine Miller	8th	Cengage	2021	Organizational Communication	P90.U840 2021	978-1-001-58380-8	Book	Classical to critical approaches in organizations. Recommended for Bachelor of Arts in Communication.	active	2026-10-08	\N	\N
22	Intercultural Communication in Contexts	Judith N. Martin and Thomas K. Nakayama	8th	McGraw-Hill	2021	Intercultural Communication	P90.V877 2021	978-1-001-66299-2	Book	Culture, power, and communication across contexts. Recommended for Bachelor of Arts in Communication.	active	2026-10-08	\N	\N
23	Strategic Writing: Multimedia Writing for Public Relations, Advertising, and More	Charles Marsh, David Guth, and Bonnie Poovey Short	5th	Routledge	2021	Public Relations	P90.W114 2021	978-1-001-74218-2	Book	Strategic message design across media platforms. Recommended for Bachelor of Arts in Communication.	active	2026-10-08	\N	\N
24	Photojournalism: The Professional's Approach	Kenneth Kobre	7th	Routledge	2017	Photojournalism	P90.X151 2017	978-1-001-82137-5	Book	Technique and storytelling in news photography. Recommended for Bachelor of Arts in Communication.	active	2026-10-08	\N	\N
25	Sound Reporting: The NPR Guide to Audio Journalism	Jonathan Kern	2nd	University of Chicago Press	2012	Broadcast Journalism	P90.Y188 2012	978-1-001-90056-8	Book	Field guide to audio journalism and podcasting. Recommended for Bachelor of Arts in Communication.	active	2026-10-08	\N	\N
26	The Art of the Documentary	Megan Cunningham	2nd	New Riders	2014	Film Studies	P90.Z225 2014	978-1-001-97975-5	Book	Craft of documentary filmmaking from idea to screen. Recommended for Bachelor of Arts in Communication.	active	2026-10-08	\N	\N
27	Development Communication: Theory and Practice	Nora C. Quebral	2nd	University of the Philippines Press	2012	Development Communication	P90.A262 2012	978-1-002-05894-7	Book	Seminal Filipino text on communication for development. Recommended for Bachelor of Arts in Communication.	active	2026-10-08	\N	\N
28	Philippine Communication Today	Crispin C. Maslog	2nd	Philippine Association of Communication Educators	2007	Philippine Media	P90.B299 2007	978-1-002-13813-7	Book	Overview of the Philippine communication landscape. Recommended for Bachelor of Arts in Communication.	active	2026-10-08	\N	\N
29	Media and Society in the Philippines	Elizabeth L. Enriquez	1st	University of the Philippines Press	2008	Philippine Media	P90.C336 2008	978-1-002-21732-0	Book	Broadcast media history and society in the Philippines. Recommended for Bachelor of Arts in Communication.	active	2026-10-08	\N	\N
30	Digital Media Ethics	Charles Ess	3rd	Polity	2020	New Media	P90.D373 2020	978-1-002-29651-6	Book	Ethics of online communication and digital life. Recommended for Bachelor of Arts in Communication.	active	2026-10-08	\N	\N
31	Social Media: A Critical Introduction	Christian Fuchs	4th	SAGE Publications	2024	New Media	P90.E410 2024	978-1-002-37570-9	Book	Critical theory of social media platforms. Recommended for Bachelor of Arts in Communication.	active	2026-10-08	\N	\N
32	The Newsroom: A Practical Guide	Melanie Moreno	1st	Anvil Publishing	2016	Journalism	P90.F447 2016	978-1-002-45489-3	Book	Newsroom workflows for student journalists. Recommended for Bachelor of Arts in Communication.	active	2026-10-08	\N	\N
33	Feature Writing: A Practical Introduction	Susan Pape and Sue Featherstone	2nd	SAGE Publications	2018	Media Writing	P90.G484 2018	978-1-002-53408-3	Book	Craft of writing features and human-interest stories. Recommended for Bachelor of Arts in Communication.	active	2026-10-08	\N	\N
34	Speech Communication Made Simple	Mylene C. Quinto	3rd	C and E Publishing	2019	Speech Communication	P90.H521 2019	978-1-002-61327-6	Book	Public speaking fundamentals for Filipino students. Recommended for Bachelor of Arts in Communication.	active	2026-10-08	\N	\N
35	Argumentation and Debate	Austin J. Freeley and David L. Steinberg	13th	Cengage	2013	Speech Communication	P90.I558 2013	978-1-002-69246-2	Book	Reasoning, briefing, and competitive debate. Recommended for Bachelor of Arts in Communication.	active	2026-10-08	\N	\N
36	The Business of Media	David Croteau and William Hoynes	4th	SAGE Publications	2022	Media Industries	P90.J595 2022	978-1-002-77165-5	Book	Ownership, economics, and power in media industries. Recommended for Bachelor of Arts in Communication.	active	2026-10-08	\N	\N
37	Community Radio in the Philippines	Louie Tabing	1st	Tambuli Foundation	2010	Philippine Media	P90.K632 2010	978-1-002-85084-8	Book	Practice of community broadcasting in the Philippines. Recommended for Bachelor of Arts in Communication.	active	2026-10-08	\N	\N
38	Media Research Methods	Anders Hansen and David Machin	2nd	Bloomsbury	2019	Communication Research	P90.L669 2019	978-1-002-93003-8	Book	Methods for studying media content and audiences. Recommended for Bachelor of Arts in Communication.	active	2026-10-08	\N	\N
39	Communication Research: Asking Questions, Finding Answers	Joann Keyton	5th	McGraw-Hill	2018	Communication Research	P90.M706 2018	978-1-003-00922-1	Book	Designing and conducting communication studies. Recommended for Bachelor of Arts in Communication.	active	2026-10-08	\N	\N
40	Crisis Communication: Theory and Practice	W. Timothy Coombs	2nd	SAGE Publications	2022	Public Relations	P90.N743 2022	978-1-003-08841-7	Book	Managing organizational crises through communication. Recommended for Bachelor of Arts in Communication.	active	2026-10-08	\N	\N
41	The Copywriter's Handbook	Robert W. Bly	4th	Holt	2020	Advertising	P90.O780 2020	978-1-003-16760-0	Book	Writing copy that sells across media. Recommended for Bachelor of Arts in Communication.	active	2026-10-08	\N	\N
42	Documentary Storytelling	Sheila Curran Bernard	5th	Routledge	2022	Film Studies	P90.P817 2022	978-1-003-24679-4	Book	Story craft for nonfiction film and video. Recommended for Bachelor of Arts in Communication.	active	2026-10-08	\N	\N
43	Mobile Journalism	Marc Blank-Settle	1st	Routledge	2019	Broadcast Journalism	P90.Q854 2019	978-1-003-32598-7	Book	Reporting and storytelling with a smartphone. Recommended for Bachelor of Arts in Communication.	active	2026-10-08	\N	\N
44	Online Journalism: Principles and Practices	Randall S. Sumpter and James W. Tankard	3rd	Routledge	2016	New Media	P90.R891 2016	978-1-003-40517-7	Book	Reporting and ethics for the web. Recommended for Bachelor of Arts in Communication.	active	2026-10-08	\N	\N
45	Theories of the Information Society	Frank Webster	4th	Routledge	2014	Media Theory	P90.S128 2014	978-1-003-48436-3	Book	Leading theories of the information age. Recommended for Bachelor of Arts in Communication.	active	2026-10-08	\N	\N
46	Rhetoric: A Very Short Introduction	Richard Toye	1st	Oxford University Press	2013	Speech Communication	P90.T165 2013	978-1-003-56355-6	Book	Concise history and theory of rhetoric. Recommended for Bachelor of Arts in Communication.	active	2026-10-08	\N	\N
47	Philippine Cinema: A History	Nick Deocampo	1st	Anvil Publishing	2011	Film Studies	P90.U202 2011	978-1-003-64274-9	Book	History of film as art and industry in the Philippines. Recommended for Bachelor of Arts in Communication.	active	2026-10-08	\N	\N
48	Media Law in the Philippines	Luis V. Teodoro	1st	University of the Philippines Press	2015	Media Law	P90.V239 2015	978-1-003-72193-2	Book	Libel, press freedom, and broadcast regulation locally. Recommended for Bachelor of Arts in Communication.	active	2026-10-08	\N	\N
49	Freedom of Expression and the Press	Raul C. Pangalangan	1st	University of the Philippines Law Center	2009	Media Law	P90.W276 2009	978-1-003-80112-2	Book	Constitutional foundations of press freedom. Recommended for Bachelor of Arts in Communication.	active	2026-10-08	\N	\N
50	Podcasting: A Practical Guide	Mia Lobel	1st	Routledge	2021	Broadcast Journalism	P90.X313 2021	978-1-003-88031-8	Book	Launching and producing narrative podcasts. Recommended for Bachelor of Arts in Communication.	active	2026-10-08	\N	\N
51	Introduction to Algorithms	Thomas H. Cormen, Charles E. Leiserson, Ronald L. Rivest, and Clifford Stein	4th	MIT Press	2022	Algorithms	QA76.Y350 2022	978-1-003-95950-2	Book	Definitive textbook on algorithms and data structures. Recommended for BS Information Systems.	active	2026-10-08	\N	\N
52	Clean Code: A Handbook of Agile Software Craftsmanship	Robert C. Martin	1st	Prentice Hall	2008	Software Engineering	QA76.Z387 2008	978-1-004-03869-5	Book	Principles and practices of readable, maintainable code. Recommended for BS Information Systems.	active	2026-10-08	\N	\N
53	The Pragmatic Programmer	David Thomas and Andrew Hunt	2nd	Addison-Wesley	2019	Software Engineering	QA76.A424 2019	978-1-004-11788-8	Book	Timeless practical advice for software developers. Recommended for BS Information Systems.	active	2026-10-08	\N	\N
54	Design Patterns: Elements of Reusable Object-Oriented Software	Erich Gamma, Richard Helm, Ralph Johnson, and John Vlissides	1st	Addison-Wesley	1994	Software Engineering	QA76.B461 1994	978-1-004-19707-1	Book	Classic catalog of object-oriented design patterns. Recommended for BS Information Systems.	active	2026-10-08	\N	\N
55	Database System Concepts	Abraham Silberschatz, Henry F. Korth, and S. Sudarshan	7th	McGraw-Hill	2019	Databases	QA76.C498 2019	978-1-004-27626-4	Book	Fundamentals of database design and systems. Recommended for BS Information Systems.	active	2026-10-08	\N	\N
56	Fundamentals of Database Systems	Ramez Elmasri and Shamkant B. Navathe	7th	Pearson	2015	Databases	QA76.D535 2015	978-1-004-35545-7	Book	Data modeling, SQL, and database theory. Recommended for BS Information Systems.	active	2026-10-08	\N	\N
57	Operating System Concepts	Abraham Silberschatz, Peter B. Galvin, and Greg Gagne	10th	Wiley	2021	Operating Systems	QA76.E572 2021	978-1-004-43464-0	Book	Processes, memory, storage, and concurrency. Recommended for BS Information Systems.	active	2026-10-08	\N	\N
58	Computer Networking: A Top-Down Approach	James F. Kurose and Keith W. Ross	8th	Pearson	2021	Networking	QA76.F609 2021	978-1-004-51383-3	Book	Internet architecture from applications downward. Recommended for BS Information Systems.	active	2026-10-08	\N	\N
59	Artificial Intelligence: A Modern Approach	Stuart Russell and Peter Norvig	4th	Pearson	2020	Artificial Intelligence	QA76.G646 2020	978-1-004-59302-6	Book	Comprehensive introduction to AI theory and methods. Recommended for BS Information Systems.	active	2026-10-08	\N	\N
60	Software Engineering	Ian Sommerville	10th	Pearson	2015	Software Engineering	QA76.H683 2015	978-1-004-67221-9	Book	Plan-driven and agile software engineering practice. Recommended for BS Information Systems.	active	2026-10-08	\N	\N
61	Systems Analysis and Design	Kenneth E. Kendall and Julie E. Kendall	11th	Pearson	2019	Systems Analysis and Design	QA76.I720 2019	978-1-004-75140-2	Book	Methods for analyzing and designing information systems. Recommended for BS Information Systems.	active	2026-10-08	\N	\N
62	Modern Systems Analysis and Design	Joseph S. Valacich and Joey F. George	9th	Pearson	2020	Systems Analysis and Design	QA76.J757 2020	978-1-004-83059-6	Book	Object-oriented systems development with UML. Recommended for BS Information Systems.	active	2026-10-08	\N	\N
63	Management Information Systems: Managing the Digital Firm	Kenneth C. Laudon and Jane P. Laudon	17th	Pearson	2023	Information Systems	QA76.K794 2023	978-1-004-90978-0	Book	Business value of enterprise information systems. Recommended for BS Information Systems.	active	2026-10-08	\N	\N
64	Information Technology Project Management	Kathy Schwalbe	9th	Cengage	2018	Project Management	QA76.L831 2018	978-1-004-98897-6	Book	Managing IT projects through the PMBOK lens. Recommended for BS Information Systems.	active	2026-10-08	\N	\N
65	A Guide to the Project Management Body of Knowledge (PMBOK Guide)	Project Management Institute	7th	Project Management Institute	2021	Project Management	QA76.M868 2021	978-1-005-06816-5	Book	Global standard for project management practice. Recommended for BS Information Systems.	active	2026-10-08	\N	\N
66	Computer Organization and Design	David A. Patterson and John L. Hennessy	6th	Morgan Kaufmann	2020	Computer Architecture	QA76.N105 2020	978-1-005-14735-8	Book	Hardware-software interface in RISC-V and MIPS. Recommended for BS Information Systems.	active	2026-10-08	\N	\N
67	Discrete Mathematics and Its Applications	Kenneth H. Rosen	8th	McGraw-Hill	2019	Discrete Mathematics	QA76.O142 2019	978-1-005-22654-1	Book	Logic, proofs, combinatorics, and graphs for computing. Recommended for BS Information Systems.	active	2026-10-08	\N	\N
68	Python Crash Course	Eric Matthes	3rd	No Starch Press	2023	Programming	QA76.P179 2023	978-1-005-30573-4	Book	Hands-on project-based introduction to Python. Recommended for BS Information Systems.	active	2026-10-08	\N	\N
69	Java: How to Program	Paul Deitel and Harvey Deitel	11th	Pearson	2017	Programming	QA76.Q216 2017	978-1-005-38492-0	Book	Java programming from basics to GUIs and web services. Recommended for BS Information Systems.	active	2026-10-08	\N	\N
70	Web Programming Step by Step	Marty Stepp, Jessica Miller, and Victoria Kirst	2nd	Lulu Press	2012	Web Development	QA76.R253 2012	978-1-005-46411-0	Book	HTML, CSS, JavaScript, and PHP for beginners. Recommended for BS Information Systems.	active	2026-10-08	\N	\N
71	Learning Web Design	Jennifer Robbins	5th	O'Reilly Media	2018	Web Development	QA76.S290 2018	978-1-005-54330-3	Book	Beginner's guide to HTML, CSS, JavaScript, and graphics. Recommended for BS Information Systems.	active	2026-10-08	\N	\N
72	Eloquent JavaScript	Marijn Haverbeke	4th	No Starch Press	2024	Web Development	QA76.T327 2024	978-1-005-62249-7	Book	Modern introduction to JavaScript programming. Recommended for BS Information Systems.	active	2026-10-08	\N	\N
73	PHP and MySQL Web Development	Luke Welling and Laura Thomson	5th	Addison-Wesley	2016	Web Development	QA76.U364 2016	978-1-005-70168-0	Book	Building database-driven websites with PHP and MySQL. Recommended for BS Information Systems.	active	2026-10-08	\N	\N
74	Data Mining: Concepts and Techniques	Jiawei Han, Micheline Kamber, and Jian Pei	4th	Morgan Kaufmann	2022	Data Science	QA76.V401 2022	978-1-005-78087-6	Book	Methods for mining large datasets. Recommended for BS Information Systems.	active	2026-10-08	\N	\N
75	Python for Data Analysis	Wes McKinney	3rd	O'Reilly Media	2022	Data Science	QA76.W438 2022	978-1-005-86006-6	Book	Data wrangling with pandas, NumPy, and Jupyter. Recommended for BS Information Systems.	active	2026-10-08	\N	\N
76	Hands-On Machine Learning with Scikit-Learn, Keras, and TensorFlow	Aurelien Geron	3rd	O'Reilly Media	2022	Machine Learning	QA76.X475 2022	978-1-005-93925-0	Book	Practical ML systems with Python frameworks. Recommended for BS Information Systems.	active	2026-10-08	\N	\N
77	Information Security: Principles and Practice	Mark Stamp	2nd	Wiley	2011	Information Security	QA76.Y512 2011	978-1-006-01844-2	Book	Access control, crypto, and software security. Recommended for BS Information Systems.	active	2026-10-08	\N	\N
78	Principles of Information Security	Michael E. Whitman and Herbert J. Mattord	7th	Cengage	2021	Information Security	QA76.Z549 2021	978-1-006-09763-8	Book	Managerial and technical foundations of infosec. Recommended for BS Information Systems.	active	2026-10-08	\N	\N
79	CompTIA Security+ Guide to Network Security Fundamentals	Mark Ciampa	7th	Cengage	2021	Information Security	QA76.A586 2021	978-1-006-17682-1	Book	Exam-aligned guide to network defense. Recommended for BS Information Systems.	active	2026-10-08	\N	\N
80	Computer Networks	Andrew S. Tanenbaum, Nick Feamster, and David J. Wetherall	6th	Pearson	2021	Networking	QA76.B623 2021	978-1-006-25601-1	Book	Layered reference on network protocols and design. Recommended for BS Information Systems.	active	2026-10-08	\N	\N
81	Cloud Computing: Concepts, Technology and Architecture	Thomas Erl, Ricardo Puttini, and Zaigham Mahmood	2nd	Prentice Hall	2023	Cloud Computing	QA76.C660 2023	978-1-006-33520-4	Book	Cloud models, mechanisms, and architectures. Recommended for BS Information Systems.	active	2026-10-08	\N	\N
82	Enterprise Architecture as Strategy	Jeanne W. Ross, Peter Weill, and David C. Robertson	1st	Harvard Business Review Press	2006	Enterprise Architecture	QA76.D697 2006	978-1-006-41439-8	Book	Building operating models on enterprise IT foundations. Recommended for BS Information Systems.	active	2026-10-08	\N	\N
83	IT Governance: How Top Performers Manage IT Decision Rights	Peter Weill and Jeanne W. Ross	1st	Harvard Business School Press	2004	IT Governance	QA76.E734 2004	978-1-006-49358-4	Book	Frameworks for governing enterprise IT. Recommended for BS Information Systems.	active	2026-10-08	\N	\N
84	Human-Computer Interaction	Alan Dix, Janet Finlay, Gregory Abowd, and Russell Beale	3rd	Pearson	2003	Human-Computer Interaction	QA76.F771 2003	978-1-006-57277-7	Book	Designing usable interactive systems. Recommended for BS Information Systems.	active	2026-10-08	\N	\N
85	Don't Make Me Think	Steve Krug	Revisited	New Riders	2014	Human-Computer Interaction	QA76.G808 2014	978-1-006-65196-0	Book	Common-sense approach to web usability. Recommended for BS Information Systems.	active	2026-10-08	\N	\N
86	The Design of Everyday Things	Don Norman	Revised	Basic Books	2013	Human-Computer Interaction	QA76.H845 2013	978-1-006-73115-0	Book	Human-centered design of objects and interfaces. Recommended for BS Information Systems.	active	2026-10-08	\N	\N
87	Agile Software Development with Scrum	Ken Schwaber and Mike Beadle	1st	Prentice Hall	2001	Software Engineering	QA76.I882 2001	978-1-006-81034-3	Book	Foundational guide to the Scrum framework. Recommended for BS Information Systems.	active	2026-10-08	\N	\N
88	User Stories Applied	Mike Cohn	1st	Addison-Wesley	2004	Software Engineering	QA76.J119 2004	978-1-006-88953-0	Book	Agile requirements through user stories. Recommended for BS Information Systems.	active	2026-10-08	\N	\N
89	Head First Design Patterns	Eric Freeman and Elisabeth Robson	2nd	O'Reilly Media	2020	Software Engineering	QA76.K156 2020	978-1-006-96872-3	Book	Brain-friendly tour of design patterns. Recommended for BS Information Systems.	active	2026-10-08	\N	\N
90	Structure and Interpretation of Computer Programs	Harold Abelson and Gerald Jay Sussman	2nd	MIT Press	1996	Programming	QA76.L193 1996	978-1-007-04791-5	Book	Foundational CS text using Scheme. Recommended for BS Information Systems.	active	2026-10-08	\N	\N
91	The C Programming Language	Brian W. Kernighan and Dennis M. Ritchie	2nd	Prentice Hall	1988	Programming	QA76.M230 1988	978-1-007-12710-5	Book	Classic reference for the C language. Recommended for BS Information Systems.	active	2026-10-08	\N	\N
92	Introduction to the Theory of Computation	Michael Sipser	3rd	Cengage	2012	Theory of Computing	QA76.N267 2012	978-1-007-20629-9	Book	Automata, computability, and complexity. Recommended for BS Information Systems.	active	2026-10-08	\N	\N
93	Data and Computer Communications	William Stallings	10th	Pearson	2017	Networking	QA76.O304 2017	978-1-007-28548-5	Book	Transmission media, protocols, and architectures. Recommended for BS Information Systems.	active	2026-10-08	\N	\N
94	Business Process Management	John Jeston	4th	Routledge	2018	Information Systems	QA76.P341 2018	978-1-007-36467-8	Book	Practical BPM framework for enterprises. Recommended for BS Information Systems.	active	2026-10-08	\N	\N
95	E-Commerce: Business, Technology, Society	Kenneth C. Laudon and Carol Guercio Traver	16th	Pearson	2020	E-Commerce	QA76.Q378 2020	978-1-007-44386-1	Book	Online business models and technologies. Recommended for BS Information Systems.	active	2026-10-08	\N	\N
96	Accounting Information Systems	Marshall B. Romney and Paul John Steinbart	15th	Pearson	2023	Information Systems	QA76.R415 2023	978-1-007-52305-1	Book	Controls and processes in AIS. Recommended for BS Information Systems.	active	2026-10-08	\N	\N
97	Systems Architecture	Stephen D. Burd	7th	Cengage	2020	Computer Architecture	QA76.S452 2020	978-1-007-60224-4	Book	Hardware, software, and enterprise architecture. Recommended for BS Information Systems.	active	2026-10-08	\N	\N
98	Ethics in Information Technology	George W. Reynolds	6th	Cengage	2018	IT Ethics	QA76.T489 2018	978-1-007-68143-0	Book	Privacy, crime, and professional ethics in IT. Recommended for BS Information Systems.	active	2026-10-08	\N	\N
99	IT Auditing: Using Controls to Protect Information Assets	Chris Davis, Mike Schiller, and Kevin Wheeler	2nd	McGraw-Hill	2011	IT Governance	QA76.U526 2011	978-1-007-76062-3	Book	Audit and control of information systems. Recommended for BS Information Systems.	active	2026-10-08	\N	\N
100	Data Science for Business	Foster Provost and Tom Fawcett	1st	O'Reilly Media	2013	Data Science	QA76.V563 2013	978-1-007-83981-7	Book	Data-analytic thinking for business decisions. Recommended for BS Information Systems.	active	2026-10-08	\N	\N
101	Calculus: Early Transcendentals	James Stewart, Daniel K. Clegg, and Saleem Watson	9th	Cengage	2020	Calculus	QA.W600 2020	978-1-007-91900-7	Book	Standard single- and multivariable calculus text. Recommended for BS Mathematics.	active	2026-10-08	\N	\N
102	Thomas' Calculus	George B. Thomas, Maurice D. Weir, and Joel R. Hass	15th	Pearson	2023	Calculus	QA.X637 2023	978-1-007-99819-4	Book	Comprehensive calculus with applications. Recommended for BS Mathematics.	active	2026-10-08	\N	\N
103	Elementary Linear Algebra	Howard Anton and Chris Rorres	11th	Wiley	2013	Linear Algebra	QA.Y674 2013	978-1-008-07738-6	Book	Vectors, matrices, and linear transformations. Recommended for BS Mathematics.	active	2026-10-08	\N	\N
104	Linear Algebra Done Right	Sheldon Axler	4th	Springer	2024	Linear Algebra	QA.Z711 2024	978-1-008-15657-9	Book	Determinant-free development of linear algebra. Recommended for BS Mathematics.	active	2026-10-08	\N	\N
105	Discrete Mathematics and Its Applications	Kenneth H. Rosen	8th	McGraw-Hill	2019	Discrete Mathematics	QA.A748 2019	978-1-008-23576-2	Book	Logic, counting, relations, and graph theory. Recommended for BS Mathematics.	active	2026-10-08	\N	\N
106	Discrete Mathematics with Applications	Susanna S. Epp	5th	Cengage	2019	Discrete Mathematics	QA.B785 2019	978-1-008-31495-5	Book	Reasoning-focused discrete mathematics. Recommended for BS Mathematics.	active	2026-10-08	\N	\N
107	How to Prove It: A Structured Approach	Daniel J. Velleman	3rd	Cambridge University Press	2019	Mathematical Proof	QA.C822 2019	978-1-008-39414-8	Book	Step-by-step guide to constructing proofs. Recommended for BS Mathematics.	active	2026-10-08	\N	\N
108	Abstract Algebra	David S. Dummit and Richard M. Foote	3rd	Wiley	2003	Abstract Algebra	QA.D859 2003	978-1-008-47333-1	Book	Groups, rings, and fields with depth. Recommended for BS Mathematics.	active	2026-10-08	\N	\N
109	A First Course in Abstract Algebra	John B. Fraleigh	8th	Pearson	2020	Abstract Algebra	QA.E896 2020	978-1-008-55252-4	Book	Accessible entry to groups, rings, and fields. Recommended for BS Mathematics.	active	2026-10-08	\N	\N
110	Contemporary Abstract Algebra	Joseph A. Gallian	10th	CRC Press	2021	Abstract Algebra	QA.F133 2021	978-1-008-63171-7	Book	Student-friendly algebra with applications. Recommended for BS Mathematics.	active	2026-10-08	\N	\N
111	Elementary Analysis: The Theory of Calculus	Kenneth A. Ross	2nd	Springer	2013	Real Analysis	QA.G170 2013	978-1-008-71090-0	Book	Rigorous foundations of single-variable analysis. Recommended for BS Mathematics.	active	2026-10-08	\N	\N
112	Understanding Analysis	Stephen Abbott	2nd	Springer	2015	Real Analysis	QA.H207 2015	978-1-008-79009-4	Book	Motivated introduction to real analysis. Recommended for BS Mathematics.	active	2026-10-08	\N	\N
113	Principles of Mathematical Analysis	Walter Rudin	3rd	McGraw-Hill	1976	Real Analysis	QA.I244 1976	978-1-008-86928-8	Book	Classic rigorous analysis text. Recommended for BS Mathematics.	active	2026-10-08	\N	\N
114	Complex Variables and Applications	James Ward Brown and Ruel V. Churchill	9th	McGraw-Hill	2013	Complex Analysis	QA.J281 2013	978-1-008-94847-1	Book	Analytic functions, residues, and mappings. Recommended for BS Mathematics.	active	2026-10-08	\N	\N
115	Elementary Differential Equations and Boundary Value Problems	William E. Boyce, Richard C. DiPrima, and Douglas B. Meade	12th	Wiley	2021	Differential Equations	QA.K318 2021	978-1-009-02766-3	Book	ODEs, systems, and boundary value problems. Recommended for BS Mathematics.	active	2026-10-08	\N	\N
116	Differential Equations with Applications	Dennis G. Zill	11th	Cengage	2024	Differential Equations	QA.L355 2024	978-1-009-10685-6	Book	Applied first course in differential equations. Recommended for BS Mathematics.	active	2026-10-08	\N	\N
117	Probability and Statistics	Morris H. DeGroot and Mark J. Schervish	4th	Pearson	2011	Probability	QA.M392 2011	978-1-009-18604-9	Book	Calculus-based probability and inference. Recommended for BS Mathematics.	active	2026-10-08	\N	\N
118	Mathematical Statistics with Applications	Dennis D. Wackerly, William Mendenhall, and Richard L. Scheaffer	7th	Cengage	2007	Statistics	QA.N429 2007	978-1-009-26523-2	Book	Applied statistical inference with theory. Recommended for BS Mathematics.	active	2026-10-08	\N	\N
119	Introductory Statistics	Neil A. Weiss	10th	Pearson	2020	Statistics	QA.O466 2020	978-1-009-34442-5	Book	Descriptive and inferential statistics. Recommended for BS Mathematics.	active	2026-10-08	\N	\N
120	Introduction to Probability Models	Sheldon M. Ross	13th	Academic Press	2023	Probability	QA.P503 2023	978-1-009-42361-8	Book	Stochastic models across disciplines. Recommended for BS Mathematics.	active	2026-10-08	\N	\N
121	Numerical Analysis	Richard L. Burden, J. Douglas Faires, and Annette M. Burden	10th	Cengage	2015	Numerical Analysis	QA.Q540 2015	978-1-009-50280-1	Book	Algorithms for scientific computation. Recommended for BS Mathematics.	active	2026-10-08	\N	\N
122	Operations Research: An Introduction	Hamdy A. Taha	10th	Pearson	2017	Operations Research	QA.R577 2017	978-1-009-58199-8	Book	Linear programming, queues, and simulation. Recommended for BS Mathematics.	active	2026-10-08	\N	\N
123	Introduction to Operations Research	Frederick S. Hillier and Gerald J. Lieberman	11th	McGraw-Hill	2021	Operations Research	QA.S614 2021	978-1-009-66118-8	Book	Optimization models and methods. Recommended for BS Mathematics.	active	2026-10-08	\N	\N
124	Topology	James R. Munkres	2nd	Pearson	2013	Topology	QA.T651 2013	978-1-009-74037-1	Book	Point-set and algebraic topology foundations. Recommended for BS Mathematics.	active	2026-10-08	\N	\N
125	Elementary Number Theory	David M. Burton	8th	McGraw-Hill	2024	Number Theory	QA.U688 2024	978-1-009-81956-5	Book	Divisibility, congruences, and Diophantine equations. Recommended for BS Mathematics.	active	2026-10-08	\N	\N
126	An Introduction to the Theory of Numbers	G. H. Hardy and E. M. Wright	6th	Oxford University Press	2008	Number Theory	QA.V725 2008	978-1-009-89875-1	Book	Classic exposition of number theory. Recommended for BS Mathematics.	active	2026-10-08	\N	\N
127	History of Mathematics	Victor J. Katz	3rd	Pearson	2008	History of Mathematics	QA.W762 2008	978-1-009-97794-4	Book	Development of mathematics across cultures. Recommended for BS Mathematics.	active	2026-10-08	\N	\N
128	Mathematics for Elementary Teachers	Tom Bassarear and Meg Moss	6th	Cengage	2019	Mathematics Education	QA.X799 2019	978-1-010-05713-0	Book	Content knowledge for teaching K-6 mathematics. Recommended for BS Mathematics.	active	2026-10-08	\N	\N
129	Teaching Secondary Mathematics	David Rock and Douglas K. Brumbaugh	5th	Routledge	2018	Mathematics Education	QA.Y836 2018	978-1-010-13632-3	Book	Methods for the high-school mathematics classroom. Recommended for BS Mathematics.	active	2026-10-08	\N	\N
130	College Geometry	David C. Kay	2nd	Pearson	2011	Geometry	QA.Z873 2011	978-1-010-21551-6	Book	Euclidean and transformational geometry. Recommended for BS Mathematics.	active	2026-10-08	\N	\N
131	Geometry: A High School Course	Serge Lang and Gene Murrow	2nd	Springer	1988	Geometry	QA.A110 1988	978-1-010-29470-2	Book	Rigorous high-school geometry. Recommended for BS Mathematics.	active	2026-10-08	\N	\N
132	Linear Programming and Network Flows	Mokhtar S. Bazaraa, John J. Jarvis, and Hanif D. Sherali	4th	Wiley	2009	Operations Research	QA.B147 2009	978-1-010-37389-6	Book	Theory and algorithms of linear optimization. Recommended for BS Mathematics.	active	2026-10-08	\N	\N
133	Mathematical Modeling	Mark M. Meerschaert	4th	Academic Press	2013	Mathematical Modeling	QA.C184 2013	978-1-010-45308-6	Book	Building models with difference and differential equations. Recommended for BS Mathematics.	active	2026-10-08	\N	\N
134	A First Course in Probability	Sheldon M. Ross	10th	Pearson	2019	Probability	QA.D221 2019	978-1-010-53227-9	Book	Undergraduate introduction to probability theory. Recommended for BS Mathematics.	active	2026-10-08	\N	\N
135	Statistics for Engineers and Scientists	William Navidi	5th	McGraw-Hill	2019	Statistics	QA.E258 2019	978-1-010-61146-2	Book	Statistics with engineering applications. Recommended for BS Mathematics.	active	2026-10-08	\N	\N
136	Mathematics of Finance	Petr Zima and Robert L. Brown	2nd	McGraw-Hill	2011	Financial Mathematics	QA.F295 2011	978-1-010-69065-8	Book	Interest, annuities, and investment mathematics. Recommended for BS Mathematics.	active	2026-10-08	\N	\N
137	An Introduction to Actuarial Mathematics	Arjun K. Gupta and Tamas Varga	1st	Springer	2013	Actuarial Science	QA.G332 2013	978-1-010-76984-2	Book	Risk, survival models, and life contingencies. Recommended for BS Mathematics.	active	2026-10-08	\N	\N
138	Graph Theory with Applications to Engineering and Computer Science	Narsingh Deo	Reprint	Dover	2016	Graph Theory	QA.H369 2016	978-1-010-84903-2	Book	Graphs, trees, and networks for applications. Recommended for BS Mathematics.	active	2026-10-08	\N	\N
139	Introduction to Graph Theory	Douglas B. West	2nd	Pearson	2000	Graph Theory	QA.I406 2000	978-1-010-92822-5	Book	Core theorems and proofs in graph theory. Recommended for BS Mathematics.	active	2026-10-08	\N	\N
140	Set Theory and Logic	Robert R. Stoll	Reprint	Dover	1979	Foundations	QA.J443 1979	978-1-011-00741-7	Book	Sets, relations, and formal logic. Recommended for BS Mathematics.	active	2026-10-08	\N	\N
141	Godel, Escher, Bach	Douglas R. Hofstadter	20th Anniversary	Basic Books	1999	Foundations	QA.K480 1999	978-1-011-08660-3	Book	Minds, machines, and mathematical meaning. Recommended for BS Mathematics.	active	2026-10-08	\N	\N
142	Fermat's Last Theorem	Simon Singh	Reprint	Anchor	1998	History of Mathematics	QA.L517 1998	978-1-011-16579-7	Book	Story of the famous conjecture and its proof. Recommended for BS Mathematics.	active	2026-10-08	\N	\N
143	The Man Who Knew Infinity	Robert Kanigel	Reprint	Washington Square Press	2015	History of Mathematics	QA.M554 2015	978-1-011-24498-0	Book	Life of mathematician Srinivasa Ramanujan. Recommended for BS Mathematics.	active	2026-10-08	\N	\N
144	Problem Solving Through Recreational Mathematics	Bonnie Averbach and Orin Chein	Reprint	Dover	1999	Problem Solving	QA.N591 1999	978-1-011-32417-0	Book	Puzzles and games that teach mathematics. Recommended for BS Mathematics.	active	2026-10-08	\N	\N
145	Trigonometry	Margaret L. Lial, John Hornsby, and David I. Schneider	11th	Pearson	2016	Trigonometry	QA.O628 2016	978-1-011-40336-3	Book	Functions, identities, and applications. Recommended for BS Mathematics.	active	2026-10-08	\N	\N
146	College Algebra	Robert F. Blitzer	8th	Pearson	2021	Algebra	QA.P665 2021	978-1-011-48255-9	Book	Functions and modeling for college students. Recommended for BS Mathematics.	active	2026-10-08	\N	\N
147	Precalculus	James Stewart, Lothar Redlin, and Saleem Watson	7th	Cengage	2015	Precalculus	QA.Q702 2015	978-1-011-56174-2	Book	Preparation for calculus with applications. Recommended for BS Mathematics.	active	2026-10-08	\N	\N
148	Math in Focus: Singapore Math	Marshall Cavendish Education	5th	Marshall Cavendish	2020	Mathematics Education	QA.R739 2020	978-1-011-64093-5	Book	Bar-model approach to school mathematics. Recommended for BS Mathematics.	active	2026-10-08	\N	\N
149	Fundamentals of Nursing: The Art and Science of Person-Centered Care	Carol R. Taylor, Pamela Lynn, and Jennifer L. Bartlett	10th	Wolters Kluwer	2022	Fundamentals of Nursing	RT.S776 2022	978-1-011-72012-5	Book	Core concepts, skills, and clinical reasoning. Recommended for BS Nursing.	active	2026-10-08	\N	\N
150	Kozier and Erb's Fundamentals of Nursing	Audrey T. Berman, Shirlee Snyder, and Geralyn Frandsen	11th	Pearson	2021	Fundamentals of Nursing	RT.T813 2021	978-1-011-79931-2	Book	Concepts, process, and practice of nursing. Recommended for BS Nursing.	active	2026-10-08	\N	\N
151	Medical-Surgical Nursing: Assessment and Management of Clinical Problems	Sharon L. Lewis, Linda Bucher, Margaret M. Heitkemper, and Mariann M. Harding	11th	Elsevier	2019	Medical-Surgical Nursing	RT.U850 2019	978-1-011-87850-5	Book	Authoritative med-surg reference for students. Recommended for BS Nursing.	active	2026-10-08	\N	\N
152	Brunner and Suddarth's Textbook of Medical-Surgical Nursing	Janice L. Hinkle, Kerry H. Cheever, and Kristen J. Overbaugh	15th	Wolters Kluwer	2021	Medical-Surgical Nursing	RT.V887 2021	978-1-011-95769-9	Book	Evidence-based adult health nursing. Recommended for BS Nursing.	active	2026-10-08	\N	\N
153	Maternal Child Nursing Care	Shannon E. Perry, Marilyn J. Hockenberry, and Deitra Leonard Lowdermilk	7th	Elsevier	2022	Maternal and Child Nursing	RT.W124 2022	978-1-012-03688-1	Book	Care of mothers, newborns, and children. Recommended for BS Nursing.	active	2026-10-08	\N	\N
154	Pediatric Nursing: The Critical Components of Nursing Care	Kathryn Rudd and Diane M. Kocisko	2nd	F. A. Davis	2018	Pediatric Nursing	RT.X161 2018	978-1-012-11607-1	Book	Growth, development, and child health nursing. Recommended for BS Nursing.	active	2026-10-08	\N	\N
155	Psychiatric-Mental Health Nursing	Sheila L. Videbeck	9th	Wolters Kluwer	2022	Psychiatric Nursing	RT.Y198 2022	978-1-012-19526-7	Book	Therapeutic communication and mental health care. Recommended for BS Nursing.	active	2026-10-08	\N	\N
156	Community and Public Health Nursing	Judith Allender, Cherie Rector, and Kristine Warner	10th	Wolters Kluwer	2023	Community Health Nursing	RT.Z235 2023	978-1-012-27445-0	Book	Population-focused nursing practice. Recommended for BS Nursing.	active	2026-10-08	\N	\N
157	Public Health Nursing: Population-Centered Health Care	Marcia Stanhope and Jeanette Lancaster	11th	Elsevier	2023	Community Health Nursing	RT.A272 2023	978-1-012-35364-3	Book	Community assessment and program planning. Recommended for BS Nursing.	active	2026-10-08	\N	\N
158	Health Assessment in Nursing	Janet R. Weber and Jane H. Kelley	7th	Wolters Kluwer	2021	Health Assessment	RT.B309 2021	978-1-012-43283-6	Book	Systematic physical examination skills. Recommended for BS Nursing.	active	2026-10-08	\N	\N
159	Physical Examination and Health Assessment	Carolyn Jarvis and Ann Eckhardt	9th	Elsevier	2023	Health Assessment	RT.C346 2023	978-1-012-51202-6	Book	Evidence-based examination techniques. Recommended for BS Nursing.	active	2026-10-08	\N	\N
160	Pharmacology and the Nursing Process	Linda Lane Lilley, Shelly Rainforth Collins, and Julie S. Snyder	10th	Elsevier	2022	Pharmacology	RT.D383 2022	978-1-012-59121-2	Book	Drug therapy integrated with the nursing process. Recommended for BS Nursing.	active	2026-10-08	\N	\N
161	Lehne's Pharmacology for Nursing Care	Jacqueline Burchum and Laura Rosenthal	11th	Elsevier	2021	Pharmacology	RT.E420 2021	978-1-012-67040-5	Book	Prototype-based pharmacology for nurses. Recommended for BS Nursing.	active	2026-10-08	\N	\N
162	Anatomy and Physiology for Nurses	Inderbir Singh	5th	Jaypee Brothers	2021	Anatomy and Physiology	RT.F457 2021	978-1-012-74959-0	Book	Body systems with clinical correlations. Recommended for BS Nursing.	active	2026-10-08	\N	\N
163	Human Anatomy and Physiology	Elaine N. Marieb and Katja Hoehn	11th	Pearson	2018	Anatomy and Physiology	RT.G494 2018	978-1-012-82878-3	Book	Illustrated two-semester A and P course text. Recommended for BS Nursing.	active	2026-10-08	\N	\N
164	Microbiology for the Healthcare Professional	Karin C. VanMeter and Robert J. Hubert	3rd	Elsevier	2021	Microbiology	RT.H531 2021	978-1-012-90797-6	Book	Pathogens and infection control for clinicians. Recommended for BS Nursing.	active	2026-10-08	\N	\N
165	Biochemistry for Nurses	Arvind S. Yadav	2nd	Jaypee Brothers	2019	Biochemistry	RT.I568 2019	978-1-012-98716-9	Book	Metabolic pathways with nursing relevance. Recommended for BS Nursing.	active	2026-10-08	\N	\N
166	Nutrition Essentials for Nursing Practice	Susan G. Dudek	9th	Wolters Kluwer	2021	Nutrition	RT.J605 2021	978-1-013-06635-1	Book	Nutrition across the lifespan and in illness. Recommended for BS Nursing.	active	2026-10-08	\N	\N
167	Nursing Research: Generating and Assessing Evidence	Denise F. Polit and Cheryl Tatano Beck	11th	Wolters Kluwer	2020	Nursing Research	RT.K642 2020	978-1-013-14554-4	Book	Reading, using, and conducting nursing research. Recommended for BS Nursing.	active	2026-10-08	\N	\N
168	Leadership and Nursing Care Management	Diane L. Huber and Maria Lindell Joseph	7th	Elsevier	2021	Nursing Leadership	RT.L679 2021	978-1-013-22473-7	Book	Management and leadership in nursing services. Recommended for BS Nursing.	active	2026-10-08	\N	\N
169	Nursing Leadership and Management	Patricia S. Yoder-Wise and Susan Sportsman	6th	Elsevier	2022	Nursing Leadership	RT.M716 2022	978-1-013-30392-0	Book	Leading teams and managing care delivery. Recommended for BS Nursing.	active	2026-10-08	\N	\N
170	Ethics and Issues in Contemporary Nursing	Margaret A. Burkhardt and Alvita K. Nathaniel	4th	Cengage	2019	Nursing Ethics	RT.N753 2019	978-1-013-38311-3	Book	Ethical reasoning in nursing dilemmas. Recommended for BS Nursing.	active	2026-10-08	\N	\N
171	Legal and Ethical Issues in Nursing	Guido W. Guinness	7th	Pearson	2019	Nursing Ethics	RT.O790 2019	978-1-013-46230-6	Book	Law, liability, and advocacy for nurses. Recommended for BS Nursing.	active	2026-10-08	\N	\N
172	Nursing Informatics and the Foundation of Knowledge	Dee McGonigle and Kathleen Mastrian	5th	Jones and Bartlett	2021	Nursing Informatics	RT.P827 2021	978-1-013-54149-0	Book	Data, information, and technology in nursing. Recommended for BS Nursing.	active	2026-10-08	\N	\N
173	Emergency Nursing: Principles and Practice	Gail P. Lenehan	1st	Elsevier	2019	Emergency Nursing	RT.Q864 2019	978-1-013-62068-3	Book	Triage and emergency department nursing. Recommended for BS Nursing.	active	2026-10-08	\N	\N
174	Critical Care Nursing: A Holistic Approach	Patricia Gonce Morton and Dorrie K. Fontaine	12th	Wolters Kluwer	2023	Critical Care Nursing	RT.R101 2023	978-1-013-69987-0	Book	Holistic management of critically ill patients. Recommended for BS Nursing.	active	2026-10-08	\N	\N
175	Gerontologic Nursing	Annette G. Lueckenotte and Mary Ann Sherman	6th	Elsevier	2021	Gerontologic Nursing	RT.S138 2021	978-1-013-77906-0	Book	Care of older adults across settings. Recommended for BS Nursing.	active	2026-10-08	\N	\N
176	Maternity and Women's Health Care	Deitra Leonard Lowdermilk, Shannon E. Perry, and Mary Catherine Cashion	13th	Elsevier	2023	Maternal and Child Nursing	RT.T175 2023	978-1-013-85825-3	Book	Evidence-based maternity nursing. Recommended for BS Nursing.	active	2026-10-08	\N	\N
177	Wong's Nursing Care of Infants and Children	Marilyn J. Hockenberry and Cheryl C. Rodgers	12th	Elsevier	2023	Pediatric Nursing	RT.U212 2023	978-1-013-93744-6	Book	Family-centered pediatric nursing. Recommended for BS Nursing.	active	2026-10-08	\N	\N
178	Davis's Drug Guide for Nurses	April Hazard Vallerand and Cynthia A. Sanoski	18th	F. A. Davis	2023	Pharmacology	RT.V249 2023	978-1-014-01663-8	Book	Quick drug reference for nursing practice. Recommended for BS Nursing.	active	2026-10-08	\N	\N
179	Nursing Diagnosis Handbook	Betty J. Ackley, Gail B. Ladwig, and Mary Beth Flynn Makic	13th	Elsevier	2022	Nursing Process	RT.W286 2022	978-1-014-09582-4	Book	Care planning with NANDA diagnoses. Recommended for BS Nursing.	active	2026-10-08	\N	\N
180	Clinical Nursing Skills and Techniques	Anne Griffin Perry, Patricia A. Potter, Wendy Ostendorf, and Nancy Laplante	11th	Elsevier	2023	Clinical Skills	RT.X323 2023	978-1-014-17501-4	Book	Step-by-step nursing procedures. Recommended for BS Nursing.	active	2026-10-08	\N	\N
181	Health Promotion Throughout the Life Span	Carole Lium Edelman and Elizabeth C. Kudzma	10th	Elsevier	2021	Health Promotion	RT.Y360 2021	978-1-014-25420-7	Book	Preventive care for every age group. Recommended for BS Nursing.	active	2026-10-08	\N	\N
182	Transcultural Nursing: Concepts, Theories, Research, and Practice	Marilyn R. McFarland and Hiba B. Wehbe-Alamah	4th	McGraw-Hill	2017	Transcultural Nursing	RT.Z397 2017	978-1-014-33339-1	Book	Culturally congruent care theory and practice. Recommended for BS Nursing.	active	2026-10-08	\N	\N
183	Disaster Nursing and Emergency Preparedness	Tener Goodwin Veenema	5th	Springer Publishing	2022	Emergency Nursing	RT.A434 2022	978-1-014-41258-4	Book	All-hazards preparedness for nurses. Recommended for BS Nursing.	active	2026-10-08	\N	\N
184	Operating Room Nursing	Nancy Girard	1st	Pearson	2012	Perioperative Nursing	RT.B471 2012	978-1-014-49177-0	Book	Perioperative roles and sterile technique. Recommended for BS Nursing.	active	2026-10-08	\N	\N
185	IV Therapy and Blood Transfusion	Lynn Hadaway	1st	Elsevier	2019	Clinical Skills	RT.C508 2019	978-1-014-57096-3	Book	Infusion practice and transfusion safety. Recommended for BS Nursing.	active	2026-10-08	\N	\N
186	Wound Care Essentials	Sharon Baranoski and Elizabeth A. Ayello	5th	Wolters Kluwer	2019	Clinical Skills	RT.D545 2019	978-1-014-65015-3	Book	Assessment and management of wounds. Recommended for BS Nursing.	active	2026-10-08	\N	\N
187	Diabetes Nursing Care	Belinda Burke	1st	Wiley-Blackwell	2012	Medical-Surgical Nursing	RT.E582 2012	978-1-014-72934-7	Book	Glycemic management and patient education. Recommended for BS Nursing.	active	2026-10-08	\N	\N
188	Oncology Nursing	Margaret Barton-Burke and Gail M. Wilkes	7th	Jones and Bartlett	2022	Medical-Surgical Nursing	RT.F619 2022	978-1-014-80853-0	Book	Cancer care across the trajectory. Recommended for BS Nursing.	active	2026-10-08	\N	\N
189	Cardiovascular Nursing	Susan L. Woods, Erika S. Sivarajan Froelicher, and Sandra Adams Motzer	8th	Wolters Kluwer	2014	Medical-Surgical Nursing	RT.G656 2014	978-1-014-88772-6	Book	Cardiac assessment and interventions. Recommended for BS Nursing.	active	2026-10-08	\N	\N
190	Respiratory Nursing	Alison Pilcher	1st	Wiley-Blackwell	2015	Medical-Surgical Nursing	RT.H693 2015	978-1-014-96691-9	Book	Pulmonary care and ventilation basics. Recommended for BS Nursing.	active	2026-10-08	\N	\N
191	Nursing Care Plans: Diagnoses, Interventions, and Outcomes	Meg Gulanick and Judith L. Myers	10th	Elsevier	2021	Nursing Process	RT.I730 2021	978-1-015-04610-8	Book	Ready-to-use care plans for clinical practice. Recommended for BS Nursing.	active	2026-10-08	\N	\N
192	Test Success: Test-Taking Techniques for Beginning Nursing Students	Patricia M. Nugent and Barbara A. Vitale	9th	F. A. Davis	2021	Nursing Education	RT.J767 2021	978-1-015-12529-2	Book	Strategies for nursing examinations. Recommended for BS Nursing.	active	2026-10-08	\N	\N
193	Saunders Comprehensive Review for the NCLEX-RN Examination	Linda Anne Silvestri and Angela Silvestri	9th	Elsevier	2022	Nursing Education	RT.K804 2022	978-1-015-20448-5	Book	Complete review for licensure examinations. Recommended for BS Nursing.	active	2026-10-08	\N	\N
194	Lippincott Q and A Review for NCLEX-RN	Diane Billings	13th	Wolters Kluwer	2022	Nursing Education	RT.L841 2022	978-1-015-28367-1	Book	Thousands of practice questions with rationales. Recommended for BS Nursing.	active	2026-10-08	\N	\N
195	Nursing Theories and Nursing Practice	Marlaine C. Smith and Marilyn E. Parker	6th	F. A. Davis	2023	Nursing Theory	RT.M878 2023	978-1-015-36286-4	Book	Major nursing theories and their application. Recommended for BS Nursing.	active	2026-10-08	\N	\N
196	Philippine Nursing Law and Jurisprudence	Carmelita C. Divinagracia	4th	C and E Publishing	2018	Nursing Ethics	RT.N115 2018	978-1-015-44205-4	Book	RA 9173 and legal responsibilities of Filipino nurses. Recommended for BS Nursing.	active	2026-10-08	\N	\N
197	Community Health Nursing in the Philippines	Celenia A. Paragas	2nd	Educational Publishing House	2010	Community Health Nursing	RT.O152 2010	978-1-015-52124-7	Book	DOH programs and barangay health practice. Recommended for BS Nursing.	active	2026-10-08	\N	\N
198	Holistic Nursing: A Handbook for Practice	Barbara Montgomery Dossey and Lynn Keegan	8th	Jones and Bartlett	2020	Holistic Nursing	RT.P189 2020	978-1-015-60043-0	Book	Integrative healing modalities in nursing. Recommended for BS Nursing.	active	2026-10-08	\N	\N
199	Foundations of Physical Education, Exercise Science, and Sport	Deborah A. Wuest and Jennifer L. Fisette	20th	McGraw-Hill	2021	Foundations of PE	GV.Q226 2021	978-1-015-67962-7	Book	History, philosophy, and careers in physical education. Recommended for Bachelor of Physical Education.	active	2026-10-08	\N	\N
200	Introduction to Physical Education, Fitness, and Sport	Daryl Siedentop and Hans van der Mars	9th	McGraw-Hill	2019	Foundations of PE	GV.R263 2019	978-1-015-75881-0	Book	Meaning and scope of movement professions. Recommended for Bachelor of Physical Education.	active	2026-10-08	\N	\N
201	Motor Learning and Performance	Richard A. Schmidt and Timothy D. Lee	6th	Human Kinetics	2019	Motor Learning	GV.S300 2019	978-1-015-83800-0	Book	Principles of skill acquisition and performance. Recommended for Bachelor of Physical Education.	active	2026-10-08	\N	\N
202	Motor Development and Learning in Physical Education	David L. Gallahue and John C. Ozmun	12th	McGraw-Hill	2019	Motor Development	GV.T337 2019	978-1-015-91719-4	Book	Lifespan motor development applied to teaching. Recommended for Bachelor of Physical Education.	active	2026-10-08	\N	\N
203	Teaching Physical Education for Learning	Judith Rink	8th	McGraw-Hill	2019	PE Pedagogy	GV.U374 2019	978-1-015-99638-0	Book	Designing effective PE lessons and units. Recommended for Bachelor of Physical Education.	active	2026-10-08	\N	\N
204	Lesson Planning for Middle School Physical Education	Michael E. Gosset	1st	Human Kinetics	2019	PE Pedagogy	GV.V411 2019	978-1-016-07557-2	Book	Standards-based lesson design for adolescents. Recommended for Bachelor of Physical Education.	active	2026-10-08	\N	\N
205	Biomechanics of Sport and Exercise	Peter M. McGinnis	4th	Human Kinetics	2020	Biomechanics	GV.W448 2020	978-1-016-15476-5	Book	Mechanical principles of human movement. Recommended for Bachelor of Physical Education.	active	2026-10-08	\N	\N
206	Basic Biomechanics	Susan J. Hall	9th	McGraw-Hill	2021	Biomechanics	GV.X485 2021	978-1-016-23395-8	Book	Qualitative and quantitative movement analysis. Recommended for Bachelor of Physical Education.	active	2026-10-08	\N	\N
207	Exercise Physiology: Nutrition, Energy, and Human Performance	William D. McArdle, Frank I. Katch, and Victor L. Katch	9th	Wolters Kluwer	2023	Exercise Physiology	GV.Y522 2023	978-1-016-31314-8	Book	Energy systems and training adaptations. Recommended for Bachelor of Physical Education.	active	2026-10-08	\N	\N
208	Physiology of Sport and Exercise	W. Larry Kenney, Jack H. Wilmore, and David L. Costill	8th	Human Kinetics	2021	Exercise Physiology	GV.Z559 2021	978-1-016-39233-4	Book	Acute and chronic responses to exercise. Recommended for Bachelor of Physical Education.	active	2026-10-08	\N	\N
209	Essentials of Strength Training and Conditioning	G. Gregory Haff and N. Travis Triplett	5th	Human Kinetics	2021	Strength and Conditioning	GV.A596 2021	978-1-016-47152-7	Book	NSCA guide to program design. Recommended for Bachelor of Physical Education.	active	2026-10-08	\N	\N
210	ACSM's Guidelines for Exercise Testing and Prescription	American College of Sports Medicine	11th	Wolters Kluwer	2021	Exercise Prescription	GV.B633 2021	978-1-016-55071-0	Book	Gold-standard fitness assessment guidelines. Recommended for Bachelor of Physical Education.	active	2026-10-08	\N	\N
211	Fitness for Life	Charles B. Corbin and Ruth Lindsey	7th	Human Kinetics	2024	Fitness	GV.C670 2024	978-1-016-62990-4	Book	Lifelong physical activity and wellness. Recommended for Bachelor of Physical Education.	active	2026-10-08	\N	\N
212	Measurement and Evaluation in Physical Education and Exercise Science	Alan C. Lacy and Skip M. Williams	8th	Routledge	2018	Assessment in PE	GV.D707 2018	978-1-016-70909-5	Book	Tests and measurement in movement sciences. Recommended for Bachelor of Physical Education.	active	2026-10-08	\N	\N
213	Adapted Physical Education and Sport	Joseph P. Winnick and David L. Porretta	7th	Human Kinetics	2021	Adapted PE	GV.E744 2021	978-1-016-78828-1	Book	Inclusive activity for persons with disabilities. Recommended for Bachelor of Physical Education.	active	2026-10-08	\N	\N
214	Sports Psychology: Concepts and Applications	Richard H. Cox	8th	McGraw-Hill	2021	Sport Psychology	GV.F781 2021	978-1-016-86747-4	Book	Motivation, anxiety, and team dynamics. Recommended for Bachelor of Physical Education.	active	2026-10-08	\N	\N
215	Foundations of Sport and Exercise Psychology	Robert S. Weinberg and Daniel Gould	8th	Human Kinetics	2023	Sport Psychology	GV.G818 2023	978-1-016-94666-7	Book	Psychological skills for athletes and coaches. Recommended for Bachelor of Physical Education.	active	2026-10-08	\N	\N
216	Nutrition for Sport and Exercise	Jackie Berning and Suzanne Nelson Steen	4th	Jones and Bartlett	2019	Sports Nutrition	GV.H855 2019	978-1-017-02585-9	Book	Fueling strategies for active people. Recommended for Bachelor of Physical Education.	active	2026-10-08	\N	\N
217	Sports Nutrition: A Handbook for Professionals	Christine Karpinski and Christine Rosenbloom	6th	Academy of Nutrition and Dietetics	2017	Sports Nutrition	GV.I892 2017	978-1-017-10504-9	Book	Evidence-based fueling for performance. Recommended for Bachelor of Physical Education.	active	2026-10-08	\N	\N
218	Coaching Principles	Rainer Martens	4th	Human Kinetics	2012	Coaching	GV.J129 2012	978-1-017-18423-5	Book	ASEP foundations of successful coaching. Recommended for Bachelor of Physical Education.	active	2026-10-08	\N	\N
219	Successful Coaching	Rainer Martens and Robin S. Vealey	5th	Human Kinetics	2024	Coaching	GV.K166 2024	978-1-017-26342-8	Book	Building character and performance in athletes. Recommended for Bachelor of Physical Education.	active	2026-10-08	\N	\N
220	Sports Officiating: A Legal Approach	Jerry Grunska	2nd	Human Kinetics	2009	Sports Management	GV.L203 2009	978-1-017-34261-1	Book	Rules, ethics, and liability in officiating. Recommended for Bachelor of Physical Education.	active	2026-10-08	\N	\N
221	Basketball: Steps to Success	Hal Wissel and Kathy Biscontini	4th	Human Kinetics	2021	Team Sports	GV.M240 2021	978-1-017-42180-4	Book	Fundamentals and drills for basketball. Recommended for Bachelor of Physical Education.	active	2026-10-08	\N	\N
222	Volleyball: Steps to Success	Becky Schmidt	2nd	Human Kinetics	2024	Team Sports	GV.N277 2024	978-1-017-50099-8	Book	Skills progression for volleyball players. Recommended for Bachelor of Physical Education.	active	2026-10-08	\N	\N
223	Football: Steps to Success	Tom Bass	2nd	Human Kinetics	2012	Team Sports	GV.O314 2012	978-1-017-58018-1	Book	Techniques and tactics for football. Recommended for Bachelor of Physical Education.	active	2026-10-08	\N	\N
224	Swimming: Steps to Success	Ernest W. Maglischo	2nd	Human Kinetics	2021	Aquatics	GV.P351 2021	978-1-017-65937-5	Book	Stroke mechanics and training sets. Recommended for Bachelor of Physical Education.	active	2026-10-08	\N	\N
225	Track and Field: Steps to Success	Gus Everett	1st	Human Kinetics	2019	Athletics	GV.Q388 2019	978-1-017-73856-8	Book	Events technique and conditioning. Recommended for Bachelor of Physical Education.	active	2026-10-08	\N	\N
226	Badminton: Steps to Success	Tony Grice	2nd	Human Kinetics	2007	Racket Sports	GV.R425 2007	978-1-017-81775-1	Book	Strokes, footwork, and strategy. Recommended for Bachelor of Physical Education.	active	2026-10-08	\N	\N
227	Tennis: Steps to Success	Jim Brown and Camilo Villegas	4th	Human Kinetics	2019	Racket Sports	GV.S462 2019	978-1-017-89694-7	Book	Groundstrokes to match play. Recommended for Bachelor of Physical Education.	active	2026-10-08	\N	\N
228	Arnis: History and Techniques of Filipino Martial Arts	Mark V. Wiley	1st	Tuttle Publishing	2012	Filipino Martial Arts	GV.T499 2012	978-1-017-97613-7	Book	National sport of the Philippines: history and basics. Recommended for Bachelor of Physical Education.	active	2026-10-08	\N	\N
229	Fundamentals of Dance	Miriam P. Aquino	2nd	Rex Book Store	2015	Dance	GV.U536 2015	978-1-018-05532-9	Book	Philippine folk, social, and creative dance. Recommended for Bachelor of Physical Education.	active	2026-10-08	\N	\N
230	Philippine Folk Dances	Francisca Reyes-Aquino	Reprint	National Book Store	2008	Dance	GV.V573 2008	978-1-018-13451-2	Book	Classic collection of Filipino folk dances. Recommended for Bachelor of Physical Education.	active	2026-10-08	\N	\N
231	Rhythmic Activities and Dance	John Price Bennett and Pamela C. Riemer	2nd	Human Kinetics	2006	Dance	GV.W610 2006	978-1-018-21370-5	Book	Teaching rhythm and movement fundamentals. Recommended for Bachelor of Physical Education.	active	2026-10-08	\N	\N
232	First Aid, CPR, and AED	American Red Cross	8th	Jones and Bartlett	2021	First Aid	GV.X647 2021	978-1-018-29289-2	Book	Emergency response knowledge and skills. Recommended for Bachelor of Physical Education.	active	2026-10-08	\N	\N
233	Care and Prevention of Athletic Injuries	William E. Prentice	10th	McGraw-Hill	2013	Sports Medicine	GV.Y684 2013	978-1-018-37208-2	Book	Recognition and rehabilitation of injuries. Recommended for Bachelor of Physical Education.	active	2026-10-08	\N	\N
234	Sports Medicine Essentials	Jim Clover and Mike Wall	3rd	Cengage	2015	Sports Medicine	GV.Z721 2015	978-1-018-45127-5	Book	Core concepts for the sports medicine team. Recommended for Bachelor of Physical Education.	active	2026-10-08	\N	\N
235	Kinesiology: Scientific Basis of Human Motion	Marilyn Hamilton, Luttgens Kinesiology	12th	McGraw-Hill	2011	Kinesiology	GV.A758 2011	978-1-018-53046-8	Book	Anatomical analysis of movement. Recommended for Bachelor of Physical Education.	active	2026-10-08	\N	\N
236	Dance Teaching Methods and Curriculum Design	Gayle Kassing and Danielle M. Jay	2nd	Human Kinetics	2020	Dance	GV.B795 2020	978-1-018-60965-2	Book	Comprehensive dance education methods. Recommended for Bachelor of Physical Education.	active	2026-10-08	\N	\N
237	Health Education: Elementary and Middle School Applications	Susan K. Telljohann, Cynthia E. Symons, and Beth Pateman	9th	McGraw-Hill	2019	Health Education	GV.C832 2019	978-1-018-68884-8	Book	School health instruction strategies. Recommended for Bachelor of Physical Education.	active	2026-10-08	\N	\N
238	Outdoor Recreation and Camping	Department of Education Philippines	1st	DepEd	2016	Outdoor Education	GV.D869 2016	978-1-018-76803-8	Book	Camping, hiking, and outdoor leadership basics. Recommended for Bachelor of Physical Education.	active	2026-10-08	\N	\N
239	Recreational Leadership	Miriam G. Reboredo	1st	Rex Book Store	2014	Recreation	GV.E106 2014	978-1-018-84722-1	Book	Planning community recreation programs. Recommended for Bachelor of Physical Education.	active	2026-10-08	\N	\N
240	Sports Management: Principles and Applications	Russell Hoye, Aaron C. T. Smith, and Matthew Nicholson	6th	Routledge	2021	Sports Management	GV.F143 2021	978-1-018-92641-4	Book	Governance and management of sport organizations. Recommended for Bachelor of Physical Education.	active	2026-10-08	\N	\N
241	Yoga Anatomy	Leslie Kaminoff and Amy Matthews	3rd	Human Kinetics	2021	Fitness	GV.G180 2021	978-1-019-00560-6	Book	Muscles and alignment in yoga postures. Recommended for Bachelor of Physical Education.	active	2026-10-08	\N	\N
242	Weight Training: Steps to Success	Thomas R. Baechle and Roger W. Earle	5th	Human Kinetics	2019	Strength and Conditioning	GV.H217 2019	978-1-019-08479-3	Book	Progressive resistance training programs. Recommended for Bachelor of Physical Education.	active	2026-10-08	\N	\N
243	Understanding Public Administration	Seung C. Lee and David H. Rosenbloom	1st	Routledge	2024	Public Administration Theory	JF.I254 2024	978-1-019-16398-6	Book	Contemporary introduction to the field. Recommended for Bachelor of Public Administration.	active	2026-10-08	\N	\N
244	Public Administration: Concepts and Cases	Richard J. Stillman II	9th	Cengage	2009	Public Administration Theory	JF.J291 2009	978-1-019-24317-6	Book	Classic cases illustrating administrative theory. Recommended for Bachelor of Public Administration.	active	2026-10-08	\N	\N
245	Classics of Public Administration	Jay M. Shafritz and Albert C. Hyde	8th	Cengage	2016	Public Administration Theory	JF.K328 2016	978-1-019-32236-9	Book	Foundational readings from Wilson to Waldo. Recommended for Bachelor of Public Administration.	active	2026-10-08	\N	\N
246	Introducing Public Administration	Jay M. Shafritz, E. W. Russell, Christopher P. Borick, and Albert C. Hyde	10th	Routledge	2022	Public Administration Theory	JF.L365 2022	978-1-019-40155-2	Book	Core functions and issues of public management. Recommended for Bachelor of Public Administration.	active	2026-10-08	\N	\N
247	Public Administration in the Philippines	Victoria A. Bautista	2nd	University of the Philippines Press	2014	Philippine Public Administration	JF.M402 2014	978-1-019-48074-8	Book	History and practice of Philippine bureaucracy. Recommended for Bachelor of Public Administration.	active	2026-10-08	\N	\N
248	Bureaucracy and Governance in the Philippines	Danilo R. Reyes	1st	University of the Philippines Press	2008	Philippine Public Administration	JF.N439 2008	978-1-019-55993-2	Book	Reform and politics of the civil service. Recommended for Bachelor of Public Administration.	active	2026-10-08	\N	\N
249	Local Government in the Philippines	Jose N. Endriga	1st	University of the Philippines Press	2001	Local Governance	JF.O476 2001	978-1-019-63912-2	Book	Decentralization under the Local Government Code. Recommended for Bachelor of Public Administration.	active	2026-10-08	\N	\N
250	The Local Government Code of 1991: Annotations	Aquilino Q. Pimentel Jr.	2nd	Rex Book Store	2013	Local Governance	JF.P513 2013	978-1-019-71831-5	Book	Annotated RA 7160 for local officials. Recommended for Bachelor of Public Administration.	active	2026-10-08	\N	\N
251	Public Policy: Politics, Analysis, and Alternatives	Michael E. Kraft and Scott R. Furlong	8th	CQ Press	2023	Public Policy	JF.Q550 2023	978-1-019-79750-1	Book	Stages and analysis of policymaking. Recommended for Bachelor of Public Administration.	active	2026-10-08	\N	\N
252	The Policy Process: A Reader	Michael S. Hill and Frederic Varone	3rd	Routledge	2021	Public Policy	JF.R587 2021	978-1-019-87669-5	Book	Key readings on agenda-setting to evaluation. Recommended for Bachelor of Public Administration.	active	2026-10-08	\N	\N
253	Policy Analysis: Concepts and Practice	David L. Weimer and Aidan R. Vining	6th	Routledge	2017	Policy Analysis	JF.S624 2017	978-1-019-95588-8	Book	Methods for analyzing policy alternatives. Recommended for Bachelor of Public Administration.	active	2026-10-08	\N	\N
254	Public Budgeting Systems	Robert D. Lee Jr., Ronald W. Johnson, and Philip G. Joyce	10th	Jones and Bartlett	2020	Public Finance	JF.T661 2020	978-1-020-03507-4	Book	Budget processes and fiscal administration. Recommended for Bachelor of Public Administration.	active	2026-10-08	\N	\N
255	Government Budgeting and Expenditure Management	Salvatore Schiavo-Campo	1st	Routledge	2017	Public Finance	JF.U698 2017	978-1-020-11426-7	Book	Budget reform and expenditure control. Recommended for Bachelor of Public Administration.	active	2026-10-08	\N	\N
256	Philippine Public Fiscal Administration	Danilo R. Reyes and Ledivina V. Carino	1st	University of the Philippines Press	2000	Public Finance	JF.V735 2000	978-1-020-19345-3	Book	Taxation, budgeting, and audit in the Philippines. Recommended for Bachelor of Public Administration.	active	2026-10-08	\N	\N
257	Human Resource Management in Public Service	Evan M. Berman, James S. Bowman, Jonathan P. West, and Montgomery R. Van Wart	6th	SAGE Publications	2020	Human Resource Management	JF.W772 2020	978-1-020-27264-6	Book	Paradoxes and practices of public HRM. Recommended for Bachelor of Public Administration.	active	2026-10-08	\N	\N
258	Public Personnel Management	Norma M. Riccucci	6th	Routledge	2021	Human Resource Management	JF.X809 2021	978-1-020-35183-9	Book	Merit systems and civil service reform. Recommended for Bachelor of Public Administration.	active	2026-10-08	\N	\N
259	Organization Theory and the Public Sector	Tom Christensen, Per Laegreid, and Kjell Arne Rovik	2nd	Routledge	2020	Organization Theory	JF.Y846 2020	978-1-020-43102-9	Book	Instrumental, cultural, and myth perspectives. Recommended for Bachelor of Public Administration.	active	2026-10-08	\N	\N
260	Understanding and Managing Public Organizations	Hal G. Rainey, Sergio Fernandez, and Deanna Malatesta	6th	Jossey-Bass	2021	Organization Theory	JF.Z883 2021	978-1-020-51021-2	Book	Behavior and management of public agencies. Recommended for Bachelor of Public Administration.	active	2026-10-08	\N	\N
261	Leadership in Public Organizations	Montgomery R. Van Wart	4th	Routledge	2022	Public Leadership	JF.A120 2022	978-1-020-58940-9	Book	Competencies for administrative leadership. Recommended for Bachelor of Public Administration.	active	2026-10-08	\N	\N
262	Administrative Law	Owen M. Fiss	1st	Foundation Press	2018	Administrative Law	JF.B157 2018	978-1-020-66859-3	Book	Judicial control of administrative action. Recommended for Bachelor of Public Administration.	active	2026-10-08	\N	\N
263	Philippine Administrative Law	Melchor G. Villanueva	3rd	Rex Book Store	2016	Administrative Law	JF.C194 2016	978-1-020-74778-6	Book	Powers and procedures of Philippine agencies. Recommended for Bachelor of Public Administration.	active	2026-10-08	\N	\N
264	Ethics in Public Management	H. George Frederickson and Richard K. Ghere	2nd	Routledge	2013	Public Ethics	JF.D231 2013	978-1-020-82697-9	Book	Administrative ethics and accountability. Recommended for Bachelor of Public Administration.	active	2026-10-08	\N	\N
265	Public Service Ethics	James S. Bowman and Jonathan P. West	2nd	Routledge	2021	Public Ethics	JF.E268 2021	978-1-020-90616-9	Book	Individual and organizational integrity. Recommended for Bachelor of Public Administration.	active	2026-10-08	\N	\N
266	Performance Management and Evaluation	Jack E. Edwards and Scott L. Lacefield	1st	SAGE Publications	2019	Public Management	JF.F305 2019	978-1-020-98535-5	Book	Measuring results in government programs. Recommended for Bachelor of Public Administration.	active	2026-10-08	\N	\N
267	 Managing Public Sector Projects	Graham M. Winch	1st	Cambridge University Press	2022	Project Management	JF.G342 2022	978-1-021-06454-7	Book	Delivering public infrastructure and programs. Recommended for Bachelor of Public Administration.	active	2026-10-08	\N	\N
268	E-Government in the Philippines	Emmanuel C. Lallana	1st	National Computer Center	2015	E-Governance	JF.H379 2015	978-1-021-14373-0	Book	Digital government initiatives and lessons. Recommended for Bachelor of Public Administration.	active	2026-10-08	\N	\N
269	Digital Government: Technology and Public Sector Performance	Darrell M. West	1st	Brookings Institution Press	2005	E-Governance	JF.I416 2005	978-1-021-22292-3	Book	How technology reshapes government services. Recommended for Bachelor of Public Administration.	active	2026-10-08	\N	\N
270	Public-Private Partnerships	E. R. Yescombe and Edward Farquharson	2nd	Elsevier	2018	Public Management	JF.J453 2018	978-1-021-30211-3	Book	Structuring PPP deals and contracts. Recommended for Bachelor of Public Administration.	active	2026-10-08	\N	\N
271	Disaster Risk Reduction and Management in the Philippines	Office of Civil Defense	1st	NDRRMC	2017	Disaster Management	JF.K490 2017	978-1-021-38130-9	Book	RA 10121 framework and local DRRM practice. Recommended for Bachelor of Public Administration.	active	2026-10-08	\N	\N
272	Introduction to Emergency Management	George Haddow, Jane Bullock, and Damon Coppola	7th	Elsevier	2020	Disaster Management	JF.L527 2020	978-1-021-46049-3	Book	Phases of emergency management. Recommended for Bachelor of Public Administration.	active	2026-10-08	\N	\N
273	Urban Planning and Governance	Pablo V. Acuna	1st	University of the Philippines Press	2012	Urban Planning	JF.M564 2012	978-1-021-53968-7	Book	Land use and city management in the Philippines. Recommended for Bachelor of Public Administration.	active	2026-10-08	\N	\N
274	The City Reader	Richard T. LeGates and Frederic Stout	7th	Routledge	2020	Urban Planning	JF.N601 2020	978-1-021-61887-0	Book	Essential urban studies anthology. Recommended for Bachelor of Public Administration.	active	2026-10-08	\N	\N
275	Development Administration	Ledivina V. Carino	1st	University of the Philippines Press	1992	Development Administration	JF.O638 1992	978-1-021-69806-3	Book	Classic Filipino text on development management. Recommended for Bachelor of Public Administration.	active	2026-10-08	\N	\N
276	New Public Management	Christopher Hood	1st	Oxford University Press	2010	Public Management	JF.P675 2010	978-1-021-77725-6	Book	Market reforms and managerialism debates. Recommended for Bachelor of Public Administration.	active	2026-10-08	\N	\N
277	Governance and Politics of the Philippines	Teresa S. Encarnacion Tadem and Noel M. Morada	1st	Oxford University Press	2006	Philippine Politics	JF.Q712 2006	978-1-021-85644-9	Book	State, regime, and governance analysis. Recommended for Bachelor of Public Administration.	active	2026-10-08	\N	\N
278	Philippine Politics and Governance	Alex B. Brillantes Jr. and Maricel T. Fernandez	2nd	University of the Philippines Press	2011	Philippine Politics	JF.R749 2011	978-1-021-93563-2	Book	Institutions and processes of Filipino governance. Recommended for Bachelor of Public Administration.	active	2026-10-08	\N	\N
279	Civil Society in the Philippines	Gerard Clarke	1st	Routledge	2013	Civil Society	JF.S786 2013	978-1-022-01482-4	Book	NGOs and people power in development. Recommended for Bachelor of Public Administration.	active	2026-10-08	\N	\N
280	Nonprofit Management	Michael J. Worth	7th	SAGE Publications	2023	Nonprofit Management	JF.T823 2023	978-1-022-09401-7	Book	Principles for mission-driven organizations. Recommended for Bachelor of Public Administration.	active	2026-10-08	\N	\N
281	Research Methods for Public Administrators	Gary Rassel, Suzanne Leland, Zachary Mohr, and Elizabeth O'Sullivan	7th	Routledge	2020	Research Methods	JF.U860 2020	978-1-022-17320-0	Book	Quantitative and qualitative methods for MPA students. Recommended for Bachelor of Public Administration.	active	2026-10-08	\N	\N
282	Statistics for Public Administration	Evan M. Berman and Xiaohu Wang	5th	SAGE Publications	2021	Statistics	JF.V897 2021	978-1-022-25239-4	Book	Applied statistics for administrators. Recommended for Bachelor of Public Administration.	active	2026-10-08	\N	\N
283	Public Procurement: Rules and Practice	Government Procurement Policy Board	1st	GPPB	2019	Procurement	JF.W134 2019	978-1-022-33158-7	Book	RA 12009 procurement rules and procedures. Recommended for Bachelor of Public Administration.	active	2026-10-08	\N	\N
284	Administrative Reforms in Asia	Jon S. T. Quah	1st	Emerald	2016	Comparative Administration	JF.X171 2016	978-1-022-41077-0	Book	Anti-corruption and reform across Asia. Recommended for Bachelor of Public Administration.	active	2026-10-08	\N	\N
285	Comparative Public Administration	Eric E. Otenyo and Nancy S. Lind	1st	Emerald	2006	Comparative Administration	JF.Y208 2006	978-1-022-48996-7	Book	Administrative systems across countries. Recommended for Bachelor of Public Administration.	active	2026-10-08	\N	\N
286	Theories of Governance	R. A. W. Rhodes	1st	Routledge	2018	Governance	JF.Z245 2018	978-1-022-56915-7	Book	Networks, hollowing out, and meta-governance. Recommended for Bachelor of Public Administration.	active	2026-10-08	\N	\N
287	Criminology: Theories, Patterns, and Typologies	Larry J. Siegel	14th	Cengage	2023	Criminology	HV.A282 2023	978-1-022-64834-0	Book	Major theories of crime causation and typologies. Recommended for BS Criminology.	active	2026-10-08	\N	\N
288	Criminology Today: An Integrative Introduction	Frank Schmalleger	10th	Pearson	2023	Criminology	HV.B319 2023	978-1-022-72753-3	Book	Contemporary overview of crime and justice. Recommended for BS Criminology.	active	2026-10-08	\N	\N
289	Introduction to Criminal Justice	Larry J. Siegel and John L. Worrall	17th	Cengage	2023	Criminal Justice	HV.C356 2023	978-1-022-80672-6	Book	Police, courts, and corrections systems. Recommended for BS Criminology.	active	2026-10-08	\N	\N
290	Criminal Justice in the Philippines	Ricardo M. Guevara	3rd	Rex Book Store	2018	Philippine Criminal Justice	HV.D393 2018	978-1-022-88591-2	Book	Five pillars of the Philippine justice system. Recommended for BS Criminology.	active	2026-10-08	\N	\N
291	The Revised Penal Code of the Philippines: Annotated	Luis B. Reyes	20th	Rex Book Store	2021	Criminal Law	HV.E430 2021	978-1-022-96510-2	Book	Standard annotation of Act No. 3815. Recommended for BS Criminology.	active	2026-10-08	\N	\N
292	Criminal Law: Fundamentals	Dean Antonio S. Bautista	1st	Rex Book Store	2017	Criminal Law	HV.F467 2017	978-1-023-04429-5	Book	Felonies, penalties, and criminal liability. Recommended for BS Criminology.	active	2026-10-08	\N	\N
293	Fundamentals of Criminal Investigation	Charles E. O'Hara and Gregory L. O'Hara	9th	Charles C. Thomas	2014	Criminal Investigation	HV.G504 2014	978-1-023-12348-8	Book	Techniques of crime detection and case building. Recommended for BS Criminology.	active	2026-10-08	\N	\N
294	Criminal Investigation	Michael D. Lyman	12th	Pearson	2023	Criminal Investigation	HV.H541 2023	978-1-023-20267-1	Book	Modern investigative methods and forensics. Recommended for BS Criminology.	active	2026-10-08	\N	\N
295	Practical Criminal Investigation	Manuel L. Quebral	2nd	Wisdom Advocate	2015	Criminal Investigation	HV.I578 2015	978-1-023-28186-7	Book	Philippine-focused investigative procedures. Recommended for BS Criminology.	active	2026-10-08	\N	\N
296	Criminalistics: An Introduction to Forensic Science	Richard Saferstein	13th	Pearson	2023	Forensic Science	HV.J615 2023	978-1-023-36105-7	Book	Crime lab methods from DNA to fingerprints. Recommended for BS Criminology.	active	2026-10-08	\N	\N
297	Forensic Science: From the Crime Scene to the Crime Lab	Richard Saferstein	4th	Pearson	2019	Forensic Science	HV.K652 2019	978-1-023-44024-0	Book	Field-to-lab forensic workflow. Recommended for BS Criminology.	active	2026-10-08	\N	\N
298	Death Investigation and Examination	R. T. B. Cruz	1st	Rex Book Store	2016	Forensic Science	HV.L689 2016	978-1-023-51943-4	Book	Medico-legal investigation in the Philippines. Recommended for BS Criminology.	active	2026-10-08	\N	\N
299	Fingerprint Identification	Ramon C. Sarmiento	2nd	Rex Book Store	2014	Dactyloscopy	HV.M726 2014	978-1-023-59862-0	Book	Classification and comparison of fingerprints. Recommended for BS Criminology.	active	2026-10-08	\N	\N
300	Questioned Documents Examination	Brenda M. Nicolas	1st	Wisdom Advocate	2013	Questioned Documents	HV.N763 2013	978-1-023-67781-3	Book	Handwriting and document fraud analysis. Recommended for BS Criminology.	active	2026-10-08	\N	\N
301	Forensic Ballistics	Felipe B. Ramos	2nd	Rex Book Store	2015	Forensic Ballistics	HV.O800 2015	978-1-023-75700-3	Book	Firearms, cartridges, and bullet comparison. Recommended for BS Criminology.	active	2026-10-08	\N	\N
302	Polygraphy: The Science of Lie Detection	Leonardo A. de Castro	1st	Wisdom Advocate	2012	Polygraphy	HV.P837 2012	978-1-023-83619-7	Book	Theory and practice of polygraph examination. Recommended for BS Criminology.	active	2026-10-08	\N	\N
303	Police Patrol Operations	Dionisio R. Flores	3rd	Rex Book Store	2017	Law Enforcement	HV.Q874 2017	978-1-023-91538-0	Book	Patrol methods and police operations. Recommended for BS Criminology.	active	2026-10-08	\N	\N
304	Police Administration and Management	Cordell W. Huey	1st	Rex Book Store	2016	Law Enforcement	HV.R111 2016	978-1-023-99457-6	Book	Organizing and leading police agencies. Recommended for BS Criminology.	active	2026-10-08	\N	\N
305	Community Policing: A Contemporary Perspective	Victor E. Kappeler and Larry K. Gaines	8th	Routledge	2020	Law Enforcement	HV.S148 2020	978-1-024-07376-8	Book	Partnership and problem-solving policing. Recommended for BS Criminology.	active	2026-10-08	\N	\N
306	Traffic Management and Accident Investigation	Carlito D. Marquez	2nd	Rex Book Store	2015	Traffic Management	HV.T185 2015	978-1-024-15295-1	Book	Enforcement and crash investigation. Recommended for BS Criminology.	active	2026-10-08	\N	\N
307	Introduction to Corrections	Robert D. Hanser	3rd	SAGE Publications	2019	Corrections	HV.U222 2019	978-1-024-23214-1	Book	Institutions, probation, and rehabilitation. Recommended for BS Criminology.	active	2026-10-08	\N	\N
308	Philippine Correctional System	Ferdinand M. Santos	1st	Rex Book Store	2016	Corrections	HV.V259 2016	978-1-024-31133-4	Book	BuCor, BJMP, and parole-probation administration. Recommended for BS Criminology.	active	2026-10-08	\N	\N
309	Probation and Parole	Howard Abadinsky	12th	Pearson	2017	Corrections	HV.W296 2017	978-1-024-39052-0	Book	Community supervision theory and practice. Recommended for BS Criminology.	active	2026-10-08	\N	\N
310	Court Testimony and Evidence	Miguel C. Contreras	1st	Central Book Supply	2014	Evidence	HV.X333 2014	978-1-024-46971-4	Book	Rules of evidence and witness examination. Recommended for BS Criminology.	active	2026-10-08	\N	\N
311	Rules of Court of the Philippines: Criminal Procedure	Supreme Court of the Philippines	A.M. Updates	Rex Book Store	2023	Criminal Procedure	HV.Y370 2023	978-1-024-54890-7	Book	Criminal procedure rules and jurisprudence. Recommended for BS Criminology.	active	2026-10-08	\N	\N
312	Human Rights and Law Enforcement	Commission on Human Rights Philippines	1st	CHR	2016	Human Rights	HV.Z407 2016	978-1-024-62809-8	Book	Rights-based policing standards. Recommended for BS Criminology.	active	2026-10-08	\N	\N
313	Vice Control and Drug Enforcement	Dangerous Drugs Board	1st	DDB	2018	Drug Enforcement	HV.A444 2018	978-1-024-70728-1	Book	RA 9165 and anti-drug operations. Recommended for BS Criminology.	active	2026-10-08	\N	\N
314	Drugs and Society	Glen R. Hanson, Peter J. Venturelli, and Annette E. Fleckenstein	14th	Jones and Bartlett	2020	Drug Education	HV.B481 2020	978-1-024-78647-7	Book	Pharmacology and policy of abused drugs. Recommended for BS Criminology.	active	2026-10-08	\N	\N
315	Criminological Theory	Frank P. Williams III and Marilyn D. McShane	7th	Pearson	2020	Criminology	HV.C518 2020	978-1-024-86566-0	Book	Classical to contemporary theory. Recommended for BS Criminology.	active	2026-10-08	\N	\N
316	Victimology: The Study of the Victim	Judy H. Eaton	1st	Routledge	2021	Victimology	HV.D555 2021	978-1-024-94485-3	Book	Victims' roles, rights, and services. Recommended for BS Criminology.	active	2026-10-08	\N	\N
317	Juvenile Delinquency	Clemens Bartollas and Stuart J. Miller	10th	Pearson	2019	Juvenile Delinquency	HV.E592 2019	978-1-025-02404-2	Book	Causes and control of youth crime. Recommended for BS Criminology.	active	2026-10-08	\N	\N
318	Juvenile Justice in the Philippines	Corazon Alma G. de Leon	1st	Rex Book Store	2013	Juvenile Delinquency	HV.F629 2013	978-1-025-10323-5	Book	RA 9344 and child-in-conflict-with-law practice. Recommended for BS Criminology.	active	2026-10-08	\N	\N
319	Terrorism and Homeland Security	Jonathan R. White	10th	Cengage	2023	Terrorism	HV.G666 2023	978-1-025-18242-1	Book	Counterterrorism strategy and policy. Recommended for BS Criminology.	active	2026-10-08	\N	\N
320	Private Security Management	Charles P. Nemeth	2nd	CRC Press	2022	Security Management	HV.H703 2022	978-1-025-26161-4	Book	Guard forces and corporate security. Recommended for BS Criminology.	active	2026-10-08	\N	\N
321	Industrial Security Management	Emmanuel Q. Villar	1st	Rex Book Store	2015	Security Management	HV.I740 2015	978-1-025-34080-7	Book	Facility and plant protection. Recommended for BS Criminology.	active	2026-10-08	\N	\N
322	Cybercrime Investigation	John Bandler and Antonia Merzon	2nd	Routledge	2023	Cybercrime	HV.J777 2023	978-1-025-41999-2	Book	Digital evidence and cyber offenses. Recommended for BS Criminology.	active	2026-10-08	\N	\N
323	Computer Forensics	Marie-Helen Maras	2nd	Jones and Bartlett	2014	Cybercrime	HV.K814 2014	978-1-025-49918-5	Book	Acquisition and analysis of digital evidence. Recommended for BS Criminology.	active	2026-10-08	\N	\N
324	Arson Investigation	Enrique T. Baking	1st	Wisdom Advocate	2014	Arson Investigation	HV.L851 2014	978-1-025-57837-8	Book	Fire cause and origin determination. Recommended for BS Criminology.	active	2026-10-08	\N	\N
325	First Aid for Law Enforcers	Philippine National Police	1st	PNP Directorate	2017	First Aid	HV.M888 2017	978-1-025-65756-1	Book	Tactical casualty care basics. Recommended for BS Criminology.	active	2026-10-08	\N	\N
326	Criminal Sociology	Isabelo R. Cristobal	1st	Rex Book Store	2012	Criminology	HV.N125 2012	978-1-025-73675-4	Book	Social roots of criminal behavior. Recommended for BS Criminology.	active	2026-10-08	\N	\N
327	Research Methods in Criminal Justice and Criminology	Frank E. Hagan and Leah E. Daigle	12th	Pearson	2023	Research Methods	HV.O162 2023	978-1-025-81594-7	Book	Designs and statistics for justice research. Recommended for BS Criminology.	active	2026-10-08	\N	\N
328	Statistics for Criminology	Avelino P. Sebastian	1st	Rex Book Store	2016	Statistics	HV.P199 2016	978-1-025-89513-0	Book	Descriptive statistics for criminology students. Recommended for BS Criminology.	active	2026-10-08	\N	\N
329	Intelligence and National Security	Wilfredo O. Garcia	1st	Rex Book Store	2015	Intelligence	HV.Q236 2015	978-1-025-97432-3	Book	Intelligence cycle and state security. Recommended for BS Criminology.	active	2026-10-08	\N	\N
330	Gun Safety and Marksmanship	NROI Philippines	1st	NROI	2019	Marksmanship	HV.R273 2019	978-1-026-05351-5	Book	Safe handling and fundamentals of shooting. Recommended for BS Criminology.	active	2026-10-08	\N	\N
331	Criminology Board Examination Reviewer	Ramon S. Garcia	6th	Rex Book Store	2022	Board Review	HV.S310 2022	978-1-026-13270-8	Book	Comprehensive licensure review questions. Recommended for BS Criminology.	active	2026-10-08	\N	\N
332	Forensic Medicine in the Philippines	Raquel B. del Rosario	1st	Central Book Supply	2011	Forensic Science	HV.T347 2011	978-1-026-21189-2	Book	Medico-legal practice and autopsy procedure. Recommended for BS Criminology.	active	2026-10-08	\N	\N
333	Developmentally Appropriate Practice in Early Childhood Programs	Sue Bredekamp and Carol Copple	4th	NAEYC	2021	Early Childhood Education	LB1140.U384 2021	978-1-026-29108-5	Book	NAEYC position statement on quality practice. Recommended for Early Childhood Education.	active	2026-10-08	\N	\N
334	The Creative Curriculum for Preschool	Diane Trister Dodge, Laura J. Colker, and Cate Heroman	6th	Teaching Strategies	2016	Early Childhood Curriculum	LB1140.V421 2016	978-1-026-37027-8	Book	Project-based preschool curriculum framework. Recommended for Early Childhood Education.	active	2026-10-08	\N	\N
335	Child Development	Laura E. Berk	7th	Pearson	2021	Child Development	LB1140.W458 2021	978-1-026-44946-2	Book	Physical, cognitive, and social development. Recommended for Early Childhood Education.	active	2026-10-08	\N	\N
336	Child Development: A Topical Approach	Robert S. Feldman	1st	Pearson	2018	Child Development	LB1140.X495 2018	978-1-026-52865-5	Book	Topical survey from infancy to adolescence. Recommended for Early Childhood Education.	active	2026-10-08	\N	\N
337	Infants, Toddlers, and Caregivers	Janet Gonzalez-Mena and Dianne Widmeyer Eyer	11th	McGraw-Hill	2020	Infant and Toddler Care	LB1140.Y532 2020	978-1-026-60784-8	Book	Relationship-based caregiving routines. Recommended for Early Childhood Education.	active	2026-10-08	\N	\N
338	Guiding Children's Social Development and Learning	Marjorie V. Fields, Patricia A. Meritt, and Deborah M. Fields	9th	Cengage	2017	Child Guidance	LB1140.Z569 2017	978-1-026-68703-1	Book	Positive guidance and classroom community. Recommended for Early Childhood Education.	active	2026-10-08	\N	\N
339	Positive Discipline in the Classroom	Jane Nelsen, Lynn Lott, and H. Stephen Glenn	4th	Harmony	2013	Child Guidance	LB1140.A606 2013	978-1-026-76622-4	Book	Class meetings and mutual respect tools. Recommended for Early Childhood Education.	active	2026-10-08	\N	\N
340	Early Childhood Literacy	Timothy Shanahan and Christopher J. Lonigan	1st	Brookes Publishing	2012	Early Literacy	LB1140.B643 2012	978-1-026-84541-7	Book	Research on preschool reading development. Recommended for Early Childhood Education.	active	2026-10-08	\N	\N
341	Beginning to Read: Thinking and Learning about Print	Marilyn Jager Adams	Reprint	MIT Press	1994	Early Literacy	LB1140.C680 1994	978-1-026-92460-0	Book	Landmark synthesis on learning to read. Recommended for Early Childhood Education.	active	2026-10-08	\N	\N
342	Teaching Mathematics in the Primary Grades	Angelica C. Mendoza	1st	Rex Book Store	2017	Early Mathematics	LB1140.D717 2017	978-1-027-00379-3	Book	Concrete-pictorial-abstract math instruction. Recommended for Early Childhood Education.	active	2026-10-08	\N	\N
343	Mathematics Learning in Early Childhood	National Research Council	1st	National Academies Press	2009	Early Mathematics	LB1140.E754 2009	978-1-027-08298-9	Book	Paths toward excellence in early math. Recommended for Early Childhood Education.	active	2026-10-08	\N	\N
344	Health, Safety, and Nutrition for the Young Child	Lynn R. Marotz	10th	Cengage	2019	Child Health and Nutrition	LB1140.F791 2019	978-1-027-16217-9	Book	Wellness practices in early childhood settings. Recommended for Early Childhood Education.	active	2026-10-08	\N	\N
345	Observing and Recording the Behavior of Young Children	Dorothy H. Cohen, Virginia Stern, and Nancy Balaban	6th	Teachers College Press	2016	Child Observation	LB1140.G828 2016	978-1-027-24136-2	Book	Anecdotal records and running records. Recommended for Early Childhood Education.	active	2026-10-08	\N	\N
346	Assessing and Guiding Young Children's Development and Learning	Oralie McAfee, Deborah J. Leong, and Elena Bodrova	6th	Pearson	2015	Assessment	LB1140.H865 2015	978-1-027-32055-5	Book	Authentic assessment in preschool. Recommended for Early Childhood Education.	active	2026-10-08	\N	\N
347	Play: How It Shapes the Brain	David Elkind	1st	Broadway Books	2007	Play	LB1140.I102 2007	978-1-027-39974-2	Book	The power of play in development. Recommended for Early Childhood Education.	active	2026-10-08	\N	\N
348	The Importance of Play in Early Childhood Education	Kristine M. Slentz	1st	Routledge	2016	Play	LB1140.J139 2016	978-1-027-47893-5	Book	Play-based learning theory and advocacy. Recommended for Early Childhood Education.	active	2026-10-08	\N	\N
349	Music and Movement for Young Children	Linda Carol Edwards, Kathleen M. Bayless, and Marjorie E. Ramsey	8th	Cengage	2017	Music and Movement	LB1140.K176 2017	978-1-027-55812-5	Book	Songs, rhythm, and creative movement. Recommended for Early Childhood Education.	active	2026-10-08	\N	\N
350	Art and Creative Development for Young Children	Robert Schirrmacher and Joan E. Fox	9th	Cengage	2020	Creative Arts	LB1140.L213 2020	978-1-027-63731-8	Book	Process art across early childhood. Recommended for Early Childhood Education.	active	2026-10-08	\N	\N
351	Science in Early Childhood	Rebecca L. Garibay	1st	Rex Book Store	2018	Early Science	LB1140.M250 2018	978-1-027-71650-1	Book	Inquiry activities for young scientists. Recommended for Early Childhood Education.	active	2026-10-08	\N	\N
352	Language Development in Early Childhood	Beverly Otto	5th	Pearson	2017	Language Development	LB1140.N287 2017	978-1-027-79569-8	Book	Stages and support of oral language. Recommended for Early Childhood Education.	active	2026-10-08	\N	\N
353	Mother Tongue-Based Multilingual Education	Department of Education Philippines	1st	DepEd	2016	Language Development	LB1140.O324 2016	978-1-027-87488-1	Book	MTB-MLE policy and classroom practice. Recommended for Early Childhood Education.	active	2026-10-08	\N	\N
354	Including Children with Special Needs	Marites P. Querol	1st	Rex Book Store	2019	Inclusive Education	LB1140.P361 2019	978-1-027-95407-1	Book	Mainstreaming in Philippine preschools. Recommended for Early Childhood Education.	active	2026-10-08	\N	\N
355	Anti-Bias Education for Young Children and Ourselves	Louise Derman-Sparks and Julie Olsen Edwards	2nd	NAEYC	2020	Diversity	LB1140.Q398 2020	978-1-028-03326-3	Book	Equity goals for early childhood programs. Recommended for Early Childhood Education.	active	2026-10-08	\N	\N
356	Families, Schools, and Communities	Donna Couchenour and Kent Chrisman	6th	Cengage	2016	Family Partnerships	LB1140.R435 2016	978-1-028-11245-6	Book	Building home-school collaboration. Recommended for Early Childhood Education.	active	2026-10-08	\N	\N
357	Parent-Teacher Partnerships	Lorna M. Espinosa	1st	Rex Book Store	2017	Family Partnerships	LB1140.S472 2017	978-1-028-19164-2	Book	Engaging Filipino families in schooling. Recommended for Early Childhood Education.	active	2026-10-08	\N	\N
358	Classroom Management for Elementary Teachers	Carolyn M. Evertson and Edmund T. Emmer	11th	Pearson	2020	Classroom Management	LB1140.T509 2020	978-1-028-27083-5	Book	Organizing productive elementary classrooms. Recommended for Early Childhood Education.	active	2026-10-08	\N	\N
359	Kindergarten Curriculum Guide	Department of Education Philippines	Revised	DepEd	2019	Curriculum	LB1140.U546 2019	978-1-028-35002-5	Book	Official Philippine kindergarten standards. Recommended for Early Childhood Education.	active	2026-10-08	\N	\N
360	Early Childhood Education in the Philippines	Fe A. Hidalgo	1st	Rex Book Store	2015	Early Childhood Education	LB1140.V583 2015	978-1-028-42921-9	Book	RA 8980 and the ECCD system. Recommended for Early Childhood Education.	active	2026-10-08	\N	\N
361	Child Psychology and Development	Evelyn M. Fernando	2nd	Rex Book Store	2018	Child Development	LB1140.W620 2018	978-1-028-50840-2	Book	Filipino-context developmental psychology. Recommended for Early Childhood Education.	active	2026-10-08	\N	\N
362	Storytelling with Children	Nancy Mellon	1st	Hawthorn Press	2013	Early Literacy	LB1140.X657 2013	978-1-028-58759-9	Book	Oral storytelling techniques for teachers. Recommended for Early Childhood Education.	active	2026-10-08	\N	\N
363	Big Books for Little Readers	Corazon S. Morilla	1st	Adarna House	2016	Early Literacy	LB1140.Y694 2016	978-1-028-66678-2	Book	Using big books in Filipino classrooms. Recommended for Early Childhood Education.	active	2026-10-08	\N	\N
364	Filipino Children's Literature	Virgilio S. Almario	1st	Adarna House	2014	Children's Literature	LB1140.Z731 2014	978-1-028-74597-5	Book	Anthology and criticism of local stories. Recommended for Early Childhood Education.	active	2026-10-08	\N	\N
365	Children's Literature in the Elementary School	Charlotte S. Huck and Barbara Kiefer	11th	McGraw-Hill	2019	Children's Literature	LB1140.A768 2019	978-1-028-82516-5	Book	Genres and selection of children's books. Recommended for Early Childhood Education.	active	2026-10-08	\N	\N
366	Teaching Beginning Reading	Rosita L. Navarro	1st	Rex Book Store	2017	Early Literacy	LB1140.B805 2017	978-1-028-90435-8	Book	Phonics and whole-language balance. Recommended for Early Childhood Education.	active	2026-10-08	\N	\N
367	Games for Early Learning	Priscilla M. Santos	1st	Rex Book Store	2016	Play	LB1140.C842 2016	978-1-028-98354-4	Book	Low-cost learning games for preschools. Recommended for Early Childhood Education.	active	2026-10-08	\N	\N
368	Nutrition for Young Children	Food and Nutrition Research Institute	1st	DOST-FNRI	2018	Child Health and Nutrition	LB1140.D879 2018	978-1-029-06273-6	Book	Pinggang Pinoy and feeding guidelines. Recommended for Early Childhood Education.	active	2026-10-08	\N	\N
369	Child Protection Policy Guide	Department of Education Philippines	1st	DepEd	2012	Child Protection	LB1140.E116 2012	978-1-029-14192-9	Book	DepEd Order 40 on child protection. Recommended for Early Childhood Education.	active	2026-10-08	\N	\N
370	Educating Young Children with Autism	Clara L. Cruz	1st	Rex Book Store	2020	Inclusive Education	LB1140.F153 2020	978-1-029-22111-9	Book	Classroom supports for learners with autism. Recommended for Early Childhood Education.	active	2026-10-08	\N	\N
371	The Whole-Brain Child	Daniel J. Siegel and Tina Payne Bryson	1st	Bantam	2012	Child Development	LB1140.G190 2012	978-1-029-30030-2	Book	Brain-based strategies for caregivers. Recommended for Early Childhood Education.	active	2026-10-08	\N	\N
372	Exceptional Children: An Introduction to Special Education	William L. Heward, Sheila R. Alber-Morgan, and Moira Konrad	12th	Pearson	2022	Special Education	LC3950.H227 2022	978-1-029-37949-0	Book	Characteristics and teaching of exceptional learners. Recommended for Special Needs Education.	active	2026-10-08	\N	\N
373	Special Education: Contemporary Perspectives for School Professionals	Marilyn Friend	6th	Pearson	2023	Special Education	LC3950.I264 2023	978-1-029-45868-3	Book	Collaboration and inclusive practices. Recommended for Special Needs Education.	active	2026-10-08	\N	\N
374	Teaching Students with Special Needs in Inclusive Settings	Tom E. C. Smith, Edward A. Polloway, James R. Patton, and Carol A. Dowdy	7th	Pearson	2019	Inclusive Education	LC3950.J301 2019	978-1-029-53787-6	Book	Adapting instruction for diverse classrooms. Recommended for Special Needs Education.	active	2026-10-08	\N	\N
375	Inclusive Education in the Philippines	Yolanda S. Quijano	1st	Rex Book Store	2016	Inclusive Education	LC3950.K338 2016	978-1-029-61706-6	Book	RA 11650 and Philippine inclusive practice. Recommended for Special Needs Education.	active	2026-10-08	\N	\N
376	Educating Children with Autism	National Research Council	1st	National Academies Press	2001	Autism	LC3950.L375 2001	978-1-029-69625-2	Book	Evidence on early autism intervention. Recommended for Special Needs Education.	active	2026-10-08	\N	\N
377	A Parent's Guide to High-Functioning Autism	Sally Ozonoff, Geraldine Dawson, and James C. McPartland	2nd	Guilford Press	2014	Autism	LC3950.M412 2014	978-1-029-77544-5	Book	Practical strategies for families and teachers. Recommended for Special Needs Education.	active	2026-10-08	\N	\N
378	Teaching Children with Autism	Marjorie H. Charlop, Russell Lang, and Mandy Rispoli	1st	Springer	2018	Autism	LC3950.N449 2018	978-1-029-85463-8	Book	Behavioral interventions in classrooms. Recommended for Special Needs Education.	active	2026-10-08	\N	\N
379	Learning Disabilities: Foundations, Characteristics, and Effective Teaching	Daniel P. Hallahan, James M. Kauffman, and Paige C. Pullen	5th	Pearson	2022	Learning Disabilities	LC3950.O486 2022	978-1-029-93382-1	Book	Identification and instruction for LD. Recommended for Special Needs Education.	active	2026-10-08	\N	\N
380	Teaching Students with Learning Disabilities	Lorna O. Hernandez	1st	Rex Book Store	2018	Learning Disabilities	LC3950.P523 2018	978-1-030-01301-7	Book	Local strategies for struggling learners. Recommended for Special Needs Education.	active	2026-10-08	\N	\N
381	ADHD: What Every Parent Needs to Know	Mark L. Wolraich and George J. DuPaul	3rd	American Academy of Pediatrics	2019	ADHD	LC3950.Q560 2019	978-1-030-09220-3	Book	Diagnosis and school supports for ADHD. Recommended for Special Needs Education.	active	2026-10-08	\N	\N
382	Teaching Young Children with ADHD	George J. DuPaul and Lee Kern	1st	Guilford Press	2011	ADHD	LC3950.R597 2011	978-1-030-17139-7	Book	Classroom interventions that work. Recommended for Special Needs Education.	active	2026-10-08	\N	\N
383	Intellectual Disability: Definition, Classification, and Systems of Supports	American Association on Intellectual and Developmental Disabilities	12th	AAIDD	2021	Intellectual Disability	LC3950.S634 2021	978-1-030-25058-0	Book	Supports-based paradigm for ID. Recommended for Special Needs Education.	active	2026-10-08	\N	\N
384	Down Syndrome: Care and Education	Teresita C. Castillo	1st	Rex Book Store	2017	Intellectual Disability	LC3950.T671 2017	978-1-030-32977-4	Book	Developmental and school guidance. Recommended for Special Needs Education.	active	2026-10-08	\N	\N
385	Hearing Impairment and Deaf Education	Marc Marschark and Patricia E. Spencer	2nd	Oxford University Press	2015	Deaf Education	LC3950.U708 2015	978-1-030-40896-7	Book	Language and literacy for deaf learners. Recommended for Special Needs Education.	active	2026-10-08	\N	\N
386	Teaching Deaf Learners	Harry Knoors and Maria Marschark	1st	Oxford University Press	2014	Deaf Education	LC3950.V745 2014	978-1-030-48815-0	Book	Psychological and educational foundations. Recommended for Special Needs Education.	active	2026-10-08	\N	\N
387	Visual Impairment: Education and Rehabilitation	Corazon B. Salazar	1st	Rex Book Store	2016	Visual Impairment	LC3950.W782 2016	978-1-030-56734-3	Book	Braille, mobility, and classroom access. Recommended for Special Needs Education.	active	2026-10-08	\N	\N
388	Physical Disabilities and Health Impairments	Elena P. Garcia	1st	Rex Book Store	2018	Physical Disabilities	LC3950.X819 2018	978-1-030-64653-6	Book	School accommodation and assistive care. Recommended for Special Needs Education.	active	2026-10-08	\N	\N
389	Gifted and Talented Learners	Sally M. Reis and Joseph S. Renzulli	1st	Routledge	2018	Gifted Education	LC3950.Y856 2018	978-1-030-72572-9	Book	Enrichment and acceleration models. Recommended for Special Needs Education.	active	2026-10-08	\N	\N
390	Teaching Gifted Children in Today's Classrooms	Susan Winebrenner and Dina Brulles	Revised	Free Spirit	2018	Gifted Education	LC3950.Z893 2018	978-1-030-80491-2	Book	Differentiation strategies that challenge. Recommended for Special Needs Education.	active	2026-10-08	\N	\N
391	Behavior Management: Principles and Practices	John J. Wheeler and David D. Richey	3rd	Pearson	2019	Behavior Management	LC3950.A130 2019	978-1-030-88410-5	Book	Positive behavior supports in schools. Recommended for Special Needs Education.	active	2026-10-08	\N	\N
392	Functional Behavioral Assessment and Intervention	Robert E. O'Neill, Richard W. Albin, Keith Storey, and Robert H. Horner	2nd	Cengage	2014	Behavior Management	LC3950.B167 2014	978-1-030-96329-9	Book	FBA process and behavior plans. Recommended for Special Needs Education.	active	2026-10-08	\N	\N
393	Assistive Technology for Students with Disabilities	Diana L. Bryant and Brian R. Bryant	5th	Pearson	2019	Assistive Technology	LC3950.C204 2019	978-1-031-04248-1	Book	Devices and software enabling access. Recommended for Special Needs Education.	active	2026-10-08	\N	\N
394	Augmentative and Alternative Communication	David R. Beukelman and Janice C. Light	5th	Brookes Publishing	2020	Assistive Technology	LC3950.D241 2020	978-1-031-12167-4	Book	AAC systems across the lifespan. Recommended for Special Needs Education.	active	2026-10-08	\N	\N
395	Speech and Language Disorders in Children	Rhea Paul, Courtenay F. Norbury, and Carolyn Gosse	6th	Elsevier	2024	Speech and Language	LC3950.E278 2024	978-1-031-20086-7	Book	Assessment and intervention for communication disorders. Recommended for Special Needs Education.	active	2026-10-08	\N	\N
396	Early Intervention for Young Children	Rosario M. Alonzo	1st	Rex Book Store	2019	Early Intervention	LC3950.F315 2019	978-1-031-28005-0	Book	Family-centered early intervention practice. Recommended for Special Needs Education.	active	2026-10-08	\N	\N
397	Individualized Education Programs	Department of Education Philippines	1st	DepEd	2020	IEP	LC3950.G352 2020	978-1-031-35924-4	Book	DepEd guidelines on IEP development. Recommended for Special Needs Education.	active	2026-10-08	\N	\N
398	Assessment in Special Education	Loraine J. Spenciner and Laura A. Cohen	1st	Pearson	2018	Assessment	LC3950.H389 2018	978-1-031-43843-7	Book	Formal and informal assessment tools. Recommended for Special Needs Education.	active	2026-10-08	\N	\N
399	Transition Planning for Students with Disabilities	Luz T. Fernandez	1st	Rex Book Store	2021	Transition	LC3950.I426 2021	978-1-031-51762-0	Book	School-to-work transition supports. Recommended for Special Needs Education.	active	2026-10-08	\N	\N
400	Counseling Families of Children with Special Needs	Rosa L. Mercado	1st	Rex Book Store	2018	Family Support	LC3950.J463 2018	978-1-031-59681-6	Book	Partnering with Filipino families. Recommended for Special Needs Education.	active	2026-10-08	\N	\N
401	Sign Language for Filipino Teachers	Philippine Federation of the Deaf	2nd	PFD	2019	Deaf Education	LC3950.K500 2019	978-1-031-67600-6	Book	Filipino Sign Language basics for classrooms. Recommended for Special Needs Education.	active	2026-10-08	\N	\N
402	Braille Literacy Manual	Resources for the Blind Philippines	1st	RBI	2017	Visual Impairment	LC3950.L537 2017	978-1-031-75519-0	Book	Reading and writing braille. Recommended for Special Needs Education.	active	2026-10-08	\N	\N
403	Occupational Therapy for Children	Jane Case-Smith and Jane Clifford O'Brien	8th	Elsevier	2019	Therapy	LC3950.M574 2019	978-1-031-83438-3	Book	OT frames of reference in pediatrics. Recommended for Special Needs Education.	active	2026-10-08	\N	\N
404	Physical Therapy for Children with Disabilities	Anita C. Benson	1st	Rex Book Store	2020	Therapy	LC3950.N611 2020	978-1-031-91357-6	Book	Movement therapy in school settings. Recommended for Special Needs Education.	active	2026-10-08	\N	\N
405	Emotional and Behavioral Disorders	Paul Zionts, Laura Zionts, and Richard L. Simpson	5th	Corwin	2016	Behavior Management	LC3950.O648 2016	978-1-031-99276-2	Book	Theory and intervention for EBD. Recommended for Special Needs Education.	active	2026-10-08	\N	\N
406	Dyslexia: A Practitioner's Handbook	Gavin Reid	5th	Wiley	2016	Learning Disabilities	LC3950.P685 2016	978-1-032-07195-4	Book	Identification and teaching for dyslexia. Recommended for Special Needs Education.	active	2026-10-08	\N	\N
407	The Out-of-Sync Child	Carol Stock Kranowitz	Revised	TarcherPerigee	2022	Sensory Processing	LC3950.Q722 2022	978-1-032-15114-4	Book	Sensory processing disorder at home and school. Recommended for Special Needs Education.	active	2026-10-08	\N	\N
408	Universal Design for Learning	Anne Meyer, David H. Rose, and David Gordon	1st	CAST	2014	Inclusive Education	LC3950.R759 2014	978-1-032-23033-7	Book	UDL framework for flexible curricula. Recommended for Special Needs Education.	active	2026-10-08	\N	\N
409	Differentiated Instruction	Carol Ann Tomlinson	3rd	ASCD	2017	Inclusive Education	LC3950.S796 2017	978-1-032-30952-1	Book	Responding to learner variance daily. Recommended for Special Needs Education. [SEEDSUP] [SEEDSUP] [SEEDSUP]	archived	2026-10-08	\N	\N
410	Dune	Frank Herbert	1st	Chilton Books	1965	Science Fiction	PS3560.Dune	9780801950773	Book	Demo capture copy	active	2026-10-12	\N	\N
411	Demo Capture Alpha	Ada Author	\N	\N	\N	\N	\N	1111111111111	Book	\N	active	2026-10-12	\N	\N
412	Demo Capture Beta	Ben Author	\N	\N	\N	\N	\N	2222222222222	Book	\N	active	2026-10-12	\N	\N
413	Demo Capture Gamma	Cat Author	\N	\N	\N	\N	\N	3333333333333	Book	\N	active	2026-10-12	\N	\N
\.


--
-- Data for Name: borrowers; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.borrowers (borrower_id, user_id, id_number, department, phone_number, borrower_status, updated_at, updated_by) FROM stdin;
56	61	SEEDREQ-002	BSN	\N	active	\N	\N
57	62	SEEDREQ-003	BACOMM	\N	active	\N	\N
58	63	SEEDREQ-101	Computing	\N	active	\N	\N
59	64	SEEDREQ-102	Nursing	\N	active	\N	\N
60	67	SEED100-001	BSIT	\N	active	\N	\N
61	68	SEED100-002	BSBA	\N	active	\N	\N
62	69	SEED100-003	BSED	\N	active	\N	\N
63	70	SEED100-004	BEED	\N	active	\N	\N
64	71	SEED100-005	BSHM	\N	active	\N	\N
65	72	SEED100-006	BS Criminology	\N	active	\N	\N
66	73	SEED100-007	BSIT	\N	active	\N	\N
67	74	SEED100-008	BSBA	\N	active	\N	\N
68	75	SEED100-009	BSED	\N	active	\N	\N
69	76	SEED100-010	BEED	\N	active	\N	\N
70	77	SEED100-011	BSHM	\N	active	\N	\N
71	78	SEED100-012	BS Criminology	\N	active	\N	\N
72	79	SEEDSUP-001	BSIS	\N	active	\N	\N
73	80	SEEDSUP-002	BSN	\N	blocked	\N	\N
74	81	SEEDSUP-003	BS Information Systems	\N	active	\N	\N
75	82	SEEDSUP-004	BS Criminology	\N	active	\N	\N
55	60	SEEDREQ-001	BSIS	+63 900 111 2222	active	2026-10-12 21:59:32.401633	60
\.


--
-- Data for Name: circulation_records; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.circulation_records (circulation_id, book_id, accession_id, borrower_id, processed_by, borrow_type, transaction_type, borrow_date, due_date, return_date, fine_amount, fine_paid, damage_notes, lost_flag, transaction_status, updated_at, updated_by) FROM stdin;
222	1	4	60	1	daily_circulation	borrow	2026-09-29	2026-09-29 00:00:00	\N	0.00	f	\N	f	active	\N	\N
223	64	901	61	1	overnight	borrow	2026-10-04	2026-10-06 00:00:00	\N	0.00	f	\N	f	active	\N	\N
224	1	2	62	1	overnight	borrow	2026-10-06	2026-10-08 00:00:00	\N	0.00	f	\N	f	active	\N	\N
225	82	1154	63	1	daily_circulation	borrow	2026-08-25	2026-08-25 00:00:00	2026-08-26	0.00	f	\N	f	returned	\N	\N
226	125	1728	64	1	daily_circulation	borrow	2026-07-01	2026-07-01 00:00:00	2026-07-02	0.00	f	\N	f	returned	\N	\N
227	1	1	65	1	overnight	borrow	2026-08-27	2026-08-29 00:00:00	2026-08-29	0.00	f	\N	f	returned	\N	\N
228	1	2	66	1	daily_circulation	borrow	2026-10-06	2026-10-06 00:00:00	2026-10-07	0.00	f	\N	f	returned	\N	\N
229	243	3176	67	1	daily_circulation	borrow	2026-10-11	2026-10-11 00:00:00	\N	0.00	f	\N	f	active	\N	\N
230	322	4155	68	1	daily_circulation	borrow	2026-07-30	2026-07-30 00:00:00	2026-08-01	0.00	f	\N	f	returned	\N	\N
231	1	3	69	1	overnight	borrow	2026-06-11	2026-07-11 00:00:00	2026-06-14	0.00	f	\N	f	returned	\N	\N
232	274	3560	70	1	overnight	borrow	2026-09-29	2026-10-29 00:00:00	\N	0.00	f	\N	f	active	\N	\N
233	328	4208	71	1	daily_circulation	borrow	2026-06-08	2026-06-08 00:00:00	2026-06-08	0.00	f	\N	f	returned	\N	\N
234	201	2677	60	1	overnight	borrow	2026-08-31	2026-09-02 00:00:00	2026-09-02	0.00	f	\N	f	returned	\N	\N
322	50	629	56	65	daily_circulation	borrow	2026-10-12	2026-10-12 23:59:00	\N	0.00	f	\N	f	active	\N	\N
236	1	5	62	1	overnight	borrow	2026-07-13	2026-07-15 00:00:00	2026-07-13	0.00	f	\N	f	returned	\N	\N
237	335	4304	63	1	daily_circulation	borrow	2026-09-12	2026-09-12 00:00:00	2026-09-13	0.00	f	\N	f	returned	\N	\N
238	61	853	64	1	daily_circulation	borrow	2026-07-02	2026-07-02 00:00:00	2026-07-04	0.00	f	\N	f	returned	\N	\N
239	348	4466	65	1	daily_circulation	borrow	2026-10-03	2026-10-03 00:00:00	2026-10-04	0.00	f	\N	f	returned	\N	\N
240	26	386	66	1	daily_circulation	borrow	2026-08-23	2026-08-23 00:00:00	2026-08-23	0.00	f	\N	f	returned	\N	\N
241	1	1	67	1	overnight	borrow	2026-09-30	2026-10-02 00:00:00	2026-09-30	0.00	f	\N	f	returned	\N	\N
242	299	3885	68	1	overnight	borrow	2026-06-19	2026-06-21 00:00:00	2026-06-19	0.00	f	\N	f	returned	\N	\N
243	154	2058	69	1	overnight	borrow	2026-06-28	2026-07-28 00:00:00	2026-07-11	0.00	f	\N	f	returned	\N	\N
244	1	5	70	1	daily_circulation	borrow	2026-08-05	2026-08-05 00:00:00	2026-08-06	0.00	f	\N	f	returned	\N	\N
245	58	778	71	1	overnight	borrow	2026-08-25	2026-09-24 00:00:00	2026-09-24	0.00	f	\N	f	returned	\N	\N
246	1	3	60	1	overnight	borrow	2026-07-27	2026-07-29 00:00:00	2026-07-29	0.00	f	\N	f	returned	\N	\N
247	1	4	61	1	daily_circulation	borrow	2026-10-10	2026-10-10 00:00:00	2026-10-12	0.00	f	\N	f	returned	\N	\N
248	10	189	62	1	daily_circulation	borrow	2026-09-20	2026-09-20 00:00:00	2026-09-22	0.00	f	\N	f	returned	\N	\N
249	17	277	63	1	daily_circulation	borrow	2026-08-26	2026-08-26 00:00:00	2026-08-28	0.00	f	\N	f	returned	\N	\N
251	197	2620	65	1	overnight	borrow	2026-06-05	2026-06-07 00:00:00	2026-06-07	0.00	f	\N	f	returned	\N	\N
252	127	1742	66	1	daily_circulation	borrow	2026-09-01	2026-09-01 00:00:00	2026-09-02	0.00	f	\N	f	returned	\N	\N
253	1	4	67	1	daily_circulation	borrow	2026-05-03	2026-05-03 00:00:00	2026-05-05	0.00	f	\N	f	returned	\N	\N
254	182	2465	68	1	daily_circulation	borrow	2026-09-10	2026-09-10 00:00:00	2026-09-10	0.00	f	\N	f	returned	\N	\N
255	1	4	69	1	daily_circulation	borrow	2026-06-24	2026-06-24 00:00:00	2026-06-24	0.00	f	\N	f	returned	\N	\N
256	259	3410	70	1	daily_circulation	borrow	2026-10-07	2026-10-07 00:00:00	2026-10-09	0.00	f	\N	f	returned	\N	\N
257	1	1	71	1	daily_circulation	borrow	2026-05-23	2026-05-23 00:00:00	2026-05-25	0.00	f	\N	f	returned	\N	\N
258	103	1395	60	1	daily_circulation	borrow	2026-07-13	2026-07-13 00:00:00	2026-07-15	0.00	f	\N	f	returned	\N	\N
259	1	4	61	1	overnight	borrow	2026-07-22	2026-07-24 00:00:00	2026-07-23	0.00	f	\N	f	returned	\N	\N
260	1	3	62	1	overnight	borrow	2026-08-15	2026-08-17 00:00:00	2026-08-17	0.00	f	\N	f	returned	\N	\N
261	1	1	63	1	daily_circulation	borrow	2026-09-10	2026-09-10 00:00:00	2026-09-11	0.00	f	\N	f	returned	\N	\N
263	14	241	65	1	daily_circulation	borrow	2026-05-11	2026-05-11 00:00:00	\N	0.00	f	\N	f	overdue	\N	\N
264	20	325	66	1	daily_circulation	borrow	2026-05-17	2026-05-17 00:00:00	2026-05-19	0.00	f	\N	f	returned	\N	\N
265	1	2	67	1	daily_circulation	borrow	2026-07-11	2026-07-11 00:00:00	2026-07-12	0.00	f	\N	f	returned	\N	\N
266	1	3	68	1	overnight	borrow	2026-10-02	2026-10-04 00:00:00	\N	0.00	f	\N	f	active	\N	\N
267	1	3	69	1	daily_circulation	borrow	2026-10-06	2026-10-06 00:00:00	2026-10-08	0.00	f	\N	f	returned	\N	\N
268	55	718	70	1	daily_circulation	borrow	2026-07-24	2026-07-24 00:00:00	2026-07-24	0.00	f	\N	f	returned	\N	\N
269	282	3635	71	1	overnight	borrow	2026-10-08	2026-11-07 00:00:00	2026-10-23	0.00	f	\N	f	returned	\N	\N
270	22	346	60	1	overnight	borrow	2026-05-27	2026-05-29 00:00:00	2026-05-27	0.00	f	\N	f	returned	\N	\N
271	265	3484	61	1	overnight	borrow	2026-07-07	2026-07-09 00:00:00	2026-07-07	0.00	f	\N	f	returned	\N	\N
272	1	2	62	1	overnight	borrow	2026-07-29	2026-07-31 00:00:00	2026-07-30	0.00	f	\N	f	returned	\N	\N
273	1	3	63	1	daily_circulation	borrow	2026-08-12	2026-08-12 00:00:00	2026-08-14	0.00	f	\N	f	returned	\N	\N
274	215	2887	64	1	overnight	borrow	2026-10-01	2026-10-03 00:00:00	2026-10-01	0.00	f	\N	f	returned	\N	\N
275	331	4245	65	1	overnight	borrow	2026-08-12	2026-08-14 00:00:00	2026-08-13	0.00	f	\N	f	returned	\N	\N
276	1	4	66	1	daily_circulation	borrow	2026-10-01	2026-10-01 00:00:00	2026-10-01	0.00	f	\N	f	returned	\N	\N
277	158	2116	67	1	daily_circulation	borrow	2026-10-03	2026-10-03 00:00:00	\N	0.00	f	\N	f	active	\N	\N
278	224	2980	68	1	overnight	borrow	2026-07-21	2026-07-23 00:00:00	2026-07-21	0.00	f	\N	f	returned	\N	\N
279	1	4	69	1	overnight	borrow	2026-10-09	2026-11-08 00:00:00	2026-10-25	0.00	f	\N	f	returned	\N	\N
280	1	1	70	1	overnight	borrow	2026-10-04	2026-11-03 00:00:00	2026-10-30	0.00	f	\N	f	returned	\N	\N
281	205	2745	71	1	daily_circulation	borrow	2026-06-30	2026-06-30 00:00:00	2026-07-01	0.00	f	\N	f	returned	\N	\N
282	1	3	60	1	overnight	borrow	2026-04-17	2026-04-19 00:00:00	2026-04-19	0.00	f	\N	f	returned	\N	\N
283	231	3068	61	1	daily_circulation	borrow	2026-07-25	2026-07-25 00:00:00	2026-07-25	0.00	f	\N	f	returned	\N	\N
284	1	3	62	1	daily_circulation	borrow	2026-09-22	2026-09-22 00:00:00	2026-09-24	0.00	f	\N	f	returned	\N	\N
285	166	2257	63	1	overnight	borrow	2026-05-05	2026-05-07 00:00:00	\N	0.00	f	\N	f	overdue	\N	\N
286	354	4530	64	1	daily_circulation	borrow	2026-04-20	2026-04-20 00:00:00	2026-04-22	0.00	f	\N	f	returned	\N	\N
287	192	2550	65	1	overnight	borrow	2026-09-23	2026-09-25 00:00:00	\N	0.00	f	\N	f	active	\N	\N
288	124	1710	66	1	overnight	borrow	2026-10-08	2026-10-10 00:00:00	\N	0.00	f	\N	f	active	\N	\N
289	321	4148	67	1	overnight	borrow	2026-10-02	2026-10-04 00:00:00	\N	0.00	f	\N	t	overdue	\N	\N
250	215	2888	64	1	overnight	borrow	2026-05-24	2026-05-26 00:00:00	\N	50.00	f	\N	t	overdue	\N	\N
290	153	2028	68	1	daily_circulation	borrow	2026-09-28	2026-09-28 00:00:00	\N	0.00	f	\N	f	active	\N	\N
291	1	1	69	1	overnight	borrow	2026-07-31	2026-08-30 00:00:00	2026-08-22	0.00	f	\N	f	returned	\N	\N
292	117	1621	70	1	daily_circulation	borrow	2026-10-08	2026-10-08 00:00:00	\N	0.00	f	\N	f	active	\N	\N
293	121	1681	71	1	overnight	borrow	2026-05-01	2026-05-31 00:00:00	2026-05-13	0.00	f	\N	f	returned	\N	\N
294	373	4729	60	1	overnight	borrow	2026-10-05	2026-10-07 00:00:00	\N	0.00	f	\N	f	active	\N	\N
295	104	1417	61	1	overnight	borrow	2026-06-30	2026-07-02 00:00:00	2026-07-01	0.00	f	\N	f	returned	\N	\N
296	1	5	62	1	daily_circulation	borrow	2026-04-22	2026-04-22 00:00:00	2026-04-22	0.00	f	\N	f	returned	\N	\N
297	1	1	63	1	daily_circulation	borrow	2026-10-07	2026-10-07 00:00:00	2026-10-07	0.00	f	\N	f	returned	\N	\N
298	1	1	64	1	daily_circulation	borrow	2026-08-16	2026-08-16 00:00:00	2026-08-18	0.00	f	\N	f	returned	\N	\N
299	301	3914	65	1	daily_circulation	borrow	2026-05-08	2026-05-08 00:00:00	2026-05-09	0.00	f	\N	f	returned	\N	\N
300	1	3	66	1	overnight	borrow	2026-09-24	2026-09-26 00:00:00	2026-09-25	0.00	f	\N	f	returned	\N	\N
301	17	279	67	1	overnight	borrow	2026-09-27	2026-09-29 00:00:00	\N	0.00	f	\N	f	active	\N	\N
302	277	3591	68	1	daily_circulation	borrow	2026-09-07	2026-09-07 00:00:00	2026-09-09	0.00	f	\N	f	returned	\N	\N
303	1	1	69	1	overnight	borrow	2026-09-23	2026-10-23 00:00:00	2026-10-05	0.00	f	\N	f	returned	\N	\N
304	97	1322	70	1	overnight	borrow	2026-09-26	2026-10-26 00:00:00	\N	0.00	f	\N	f	active	\N	\N
305	287	3690	71	1	daily_circulation	borrow	2026-07-16	2026-07-16 00:00:00	\N	0.00	f	\N	f	overdue	\N	\N
306	212	2853	60	1	daily_circulation	borrow	2026-05-14	2026-05-14 00:00:00	\N	0.00	f	\N	f	overdue	\N	\N
307	152	2014	61	1	overnight	borrow	2026-10-03	2026-10-05 00:00:00	\N	0.00	f	\N	f	active	\N	\N
308	1	3	62	1	overnight	borrow	2026-07-24	2026-07-26 00:00:00	2026-07-25	0.00	f	\N	f	returned	\N	\N
309	322	4158	63	1	overnight	borrow	2026-05-03	2026-05-05 00:00:00	2026-05-03	0.00	f	\N	f	returned	\N	\N
310	1	4	64	1	overnight	borrow	2026-09-22	2026-09-24 00:00:00	2026-09-22	0.00	f	\N	f	returned	\N	\N
311	142	1882	65	1	overnight	borrow	2026-08-01	2026-08-03 00:00:00	\N	0.00	f	\N	f	overdue	\N	\N
312	381	4834	66	1	daily_circulation	borrow	2026-08-02	2026-08-02 00:00:00	2026-08-03	0.00	f	\N	f	returned	\N	\N
313	360	4593	67	1	daily_circulation	borrow	2026-06-25	2026-06-25 00:00:00	2026-06-26	0.00	f	\N	f	returned	\N	\N
314	13	229	68	1	daily_circulation	borrow	2026-10-02	2026-10-02 00:00:00	\N	0.00	f	\N	f	active	\N	\N
315	213	2863	69	1	overnight	borrow	2026-07-09	2026-08-08 00:00:00	2026-08-05	0.00	f	\N	f	returned	\N	\N
316	69	976	70	1	daily_circulation	borrow	2026-09-22	2026-09-22 00:00:00	2026-09-22	0.00	f	\N	f	returned	\N	\N
317	352	4512	71	1	daily_circulation	borrow	2026-10-03	2026-10-03 00:00:00	\N	0.00	f	\N	f	active	\N	\N
318	1	1	60	1	daily_circulation	borrow	2026-07-19	2026-07-19 00:00:00	2026-07-21	0.00	f	\N	f	returned	\N	\N
319	1	5	61	1	daily_circulation	borrow	2026-10-01	2026-10-01 00:00:00	2026-10-01	0.00	f	\N	f	returned	\N	\N
320	1	4	62	1	overnight	borrow	2026-05-19	2026-05-21 00:00:00	2026-05-21	0.00	f	\N	f	returned	\N	\N
321	1	5	63	1	daily_circulation	borrow	2026-05-24	2026-05-24 00:00:00	2026-05-24	0.00	f	\N	f	returned	\N	\N
323	101	1347	55	60	daily_circulation	borrow	2026-10-12	2026-10-12 23:59:00	2026-10-12	0.00	f	\N	f	returned	2026-10-12 21:59:24.307982	65
235	1	1	61	1	daily_circulation	borrow	2026-05-13	2026-05-13 00:00:00	\N	25.00	f	\N	f	overdue	\N	\N
262	120	1668	64	1	overnight	borrow	2026-06-08	2026-06-10 00:00:00	\N	75.00	t	\N	f	overdue	\N	\N
\.


--
-- Data for Name: departments; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.departments (department_id, name, dept_type, status) FROM stdin;
1	Bachelor of Arts in Communication	program	active
2	BS Information Systems	program	active
3	BS Mathematics	program	active
4	BS Nursing	program	active
5	Bachelor of Physical Education	program	active
6	Bachelor of Public Administration	program	active
7	BS Criminology	program	active
8	Early Childhood Education	program	active
9	Special Needs Education	program	active
\.


--
-- Data for Name: inventory_sessions; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.inventory_sessions (session_id, librarian_id, total_books, scanned_count, session_status, started_at, ended_at, updated_at, updated_by) FROM stdin;
1	1	100	12	active	2026-10-08 00:54:18.355751	\N	\N	\N
2	1	100	100	completed	2026-10-08 00:54:18.355751	2026-10-08 00:54:18.355751	\N	\N
3	65	5104	2	completed	2026-10-12 00:00:00	2026-10-12 00:00:00	2026-10-12 21:59:32.144548	65
\.


--
-- Data for Name: inventory_status; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.inventory_status (inventory_id, accession_id, inventory_state, inventory_type, checked_by, last_checked_date, session_id, notes) FROM stdin;
69	1	missing	realtime_scan	65	2026-10-12	3	\N
70	2	borrowed	realtime_scan	65	2026-10-12	3	\N
71	3	borrowed	realtime_scan	65	2026-10-12	3	\N
72	4	borrowed	realtime_scan	65	2026-10-12	3	\N
73	5	missing	realtime_scan	65	2026-10-12	3	\N
74	6	missing	realtime_scan	65	2026-10-12	3	\N
75	7	missing	realtime_scan	65	2026-10-12	3	\N
76	8	missing	realtime_scan	65	2026-10-12	3	\N
77	9	missing	realtime_scan	65	2026-10-12	3	\N
78	10	missing	realtime_scan	65	2026-10-12	3	\N
79	11	missing	realtime_scan	65	2026-10-12	3	\N
80	12	missing	realtime_scan	65	2026-10-12	3	\N
81	13	missing	realtime_scan	65	2026-10-12	3	\N
82	14	missing	realtime_scan	65	2026-10-12	3	\N
83	15	missing	realtime_scan	65	2026-10-12	3	\N
84	16	missing	realtime_scan	65	2026-10-12	3	\N
85	17	missing	realtime_scan	65	2026-10-12	3	\N
86	18	missing	realtime_scan	65	2026-10-12	3	\N
87	19	missing	realtime_scan	65	2026-10-12	3	\N
88	20	missing	realtime_scan	65	2026-10-12	3	\N
89	21	missing	realtime_scan	65	2026-10-12	3	\N
90	22	missing	realtime_scan	65	2026-10-12	3	\N
91	23	missing	realtime_scan	65	2026-10-12	3	\N
92	24	missing	realtime_scan	65	2026-10-12	3	\N
95	27	missing	realtime_scan	65	2026-10-12	3	\N
96	28	missing	realtime_scan	65	2026-10-12	3	\N
101	33	missing	annual_physical	65	2026-10-12	3	\N
102	34	missing	annual_physical	65	2026-10-12	3	\N
105	35	missing	annual_physical	65	2026-10-12	3	\N
106	36	missing	annual_physical	65	2026-10-12	3	\N
107	37	missing	annual_physical	65	2026-10-12	3	\N
108	38	missing	annual_physical	65	2026-10-12	3	\N
109	39	missing	annual_physical	65	2026-10-12	3	\N
110	40	missing	annual_physical	65	2026-10-12	3	\N
111	41	missing	annual_physical	65	2026-10-12	3	\N
112	42	missing	annual_physical	65	2026-10-12	3	\N
113	43	missing	annual_physical	65	2026-10-12	3	\N
114	44	missing	annual_physical	65	2026-10-12	3	\N
115	45	missing	annual_physical	65	2026-10-12	3	\N
116	46	missing	annual_physical	65	2026-10-12	3	\N
117	47	missing	annual_physical	65	2026-10-12	3	\N
118	48	missing	annual_physical	65	2026-10-12	3	\N
119	49	missing	annual_physical	65	2026-10-12	3	\N
120	50	missing	annual_physical	65	2026-10-12	3	\N
121	51	missing	annual_physical	65	2026-10-12	3	\N
122	52	missing	annual_physical	65	2026-10-12	3	\N
123	53	missing	annual_physical	65	2026-10-12	3	\N
124	54	missing	annual_physical	65	2026-10-12	3	\N
125	55	missing	annual_physical	65	2026-10-12	3	\N
126	56	missing	annual_physical	65	2026-10-12	3	\N
127	57	missing	annual_physical	65	2026-10-12	3	\N
128	58	missing	annual_physical	65	2026-10-12	3	\N
129	59	missing	annual_physical	65	2026-10-12	3	\N
130	60	missing	annual_physical	65	2026-10-12	3	\N
131	61	missing	annual_physical	65	2026-10-12	3	\N
132	62	missing	annual_physical	65	2026-10-12	3	\N
133	63	missing	annual_physical	65	2026-10-12	3	\N
134	64	missing	annual_physical	65	2026-10-12	3	\N
135	65	missing	annual_physical	65	2026-10-12	3	\N
136	66	missing	annual_physical	65	2026-10-12	3	\N
137	67	missing	annual_physical	65	2026-10-12	3	\N
138	68	missing	annual_physical	65	2026-10-12	3	\N
139	69	missing	annual_physical	65	2026-10-12	3	\N
140	70	missing	annual_physical	65	2026-10-12	3	\N
141	71	missing	annual_physical	65	2026-10-12	3	\N
142	72	missing	annual_physical	65	2026-10-12	3	\N
93	25	damaged	realtime_scan	1	2026-10-12	\N	SEED100
94	26	damaged	realtime_scan	1	2026-10-12	\N	SEED100
97	29	lost	realtime_scan	1	2026-10-12	\N	SEED100
98	30	lost	realtime_scan	1	2026-10-12	\N	SEED100
99	31	lost	annual_physical	1	2026-10-12	1	SEEDSUP
100	32	damaged	annual_physical	1	2026-10-12	1	SEEDSUP
143	73	missing	annual_physical	65	2026-10-12	3	\N
144	74	missing	annual_physical	65	2026-10-12	3	\N
145	75	missing	annual_physical	65	2026-10-12	3	\N
146	76	missing	annual_physical	65	2026-10-12	3	\N
147	77	missing	annual_physical	65	2026-10-12	3	\N
148	78	missing	annual_physical	65	2026-10-12	3	\N
149	79	missing	annual_physical	65	2026-10-12	3	\N
150	80	missing	annual_physical	65	2026-10-12	3	\N
151	81	missing	annual_physical	65	2026-10-12	3	\N
152	82	missing	annual_physical	65	2026-10-12	3	\N
153	83	missing	annual_physical	65	2026-10-12	3	\N
154	84	missing	annual_physical	65	2026-10-12	3	\N
155	85	missing	annual_physical	65	2026-10-12	3	\N
156	86	missing	annual_physical	65	2026-10-12	3	\N
157	87	missing	annual_physical	65	2026-10-12	3	\N
158	88	missing	annual_physical	65	2026-10-12	3	\N
159	89	missing	annual_physical	65	2026-10-12	3	\N
160	90	missing	annual_physical	65	2026-10-12	3	\N
161	91	missing	annual_physical	65	2026-10-12	3	\N
162	92	missing	annual_physical	65	2026-10-12	3	\N
163	93	missing	annual_physical	65	2026-10-12	3	\N
164	94	missing	annual_physical	65	2026-10-12	3	\N
165	95	missing	annual_physical	65	2026-10-12	3	\N
166	96	missing	annual_physical	65	2026-10-12	3	\N
167	97	missing	annual_physical	65	2026-10-12	3	\N
168	98	missing	annual_physical	65	2026-10-12	3	\N
169	99	missing	annual_physical	65	2026-10-12	3	\N
170	100	missing	annual_physical	65	2026-10-12	3	\N
171	101	missing	annual_physical	65	2026-10-12	3	\N
172	102	missing	annual_physical	65	2026-10-12	3	\N
173	103	missing	annual_physical	65	2026-10-12	3	\N
103	5101	available	annual_physical	65	2026-10-12	3	\N
174	104	missing	annual_physical	65	2026-10-12	3	\N
175	105	missing	annual_physical	65	2026-10-12	3	\N
176	106	missing	annual_physical	65	2026-10-12	3	\N
177	107	missing	annual_physical	65	2026-10-12	3	\N
178	108	missing	annual_physical	65	2026-10-12	3	\N
179	109	missing	annual_physical	65	2026-10-12	3	\N
180	110	missing	annual_physical	65	2026-10-12	3	\N
181	111	missing	annual_physical	65	2026-10-12	3	\N
182	112	missing	annual_physical	65	2026-10-12	3	\N
183	113	missing	annual_physical	65	2026-10-12	3	\N
184	114	missing	annual_physical	65	2026-10-12	3	\N
185	115	missing	annual_physical	65	2026-10-12	3	\N
186	116	missing	annual_physical	65	2026-10-12	3	\N
187	117	missing	annual_physical	65	2026-10-12	3	\N
188	118	missing	annual_physical	65	2026-10-12	3	\N
189	119	missing	annual_physical	65	2026-10-12	3	\N
190	120	missing	annual_physical	65	2026-10-12	3	\N
191	121	missing	annual_physical	65	2026-10-12	3	\N
192	122	missing	annual_physical	65	2026-10-12	3	\N
193	123	missing	annual_physical	65	2026-10-12	3	\N
194	124	missing	annual_physical	65	2026-10-12	3	\N
195	125	missing	annual_physical	65	2026-10-12	3	\N
196	126	missing	annual_physical	65	2026-10-12	3	\N
197	127	missing	annual_physical	65	2026-10-12	3	\N
198	128	missing	annual_physical	65	2026-10-12	3	\N
199	129	missing	annual_physical	65	2026-10-12	3	\N
200	130	missing	annual_physical	65	2026-10-12	3	\N
201	131	missing	annual_physical	65	2026-10-12	3	\N
202	132	missing	annual_physical	65	2026-10-12	3	\N
203	133	missing	annual_physical	65	2026-10-12	3	\N
204	134	missing	annual_physical	65	2026-10-12	3	\N
205	135	missing	annual_physical	65	2026-10-12	3	\N
206	136	missing	annual_physical	65	2026-10-12	3	\N
207	137	missing	annual_physical	65	2026-10-12	3	\N
208	138	missing	annual_physical	65	2026-10-12	3	\N
209	139	missing	annual_physical	65	2026-10-12	3	\N
210	140	missing	annual_physical	65	2026-10-12	3	\N
211	141	missing	annual_physical	65	2026-10-12	3	\N
212	142	missing	annual_physical	65	2026-10-12	3	\N
213	143	missing	annual_physical	65	2026-10-12	3	\N
214	144	missing	annual_physical	65	2026-10-12	3	\N
215	145	missing	annual_physical	65	2026-10-12	3	\N
216	146	missing	annual_physical	65	2026-10-12	3	\N
217	147	missing	annual_physical	65	2026-10-12	3	\N
218	148	missing	annual_physical	65	2026-10-12	3	\N
219	149	missing	annual_physical	65	2026-10-12	3	\N
220	150	missing	annual_physical	65	2026-10-12	3	\N
221	151	missing	annual_physical	65	2026-10-12	3	\N
222	152	missing	annual_physical	65	2026-10-12	3	\N
223	153	missing	annual_physical	65	2026-10-12	3	\N
224	154	missing	annual_physical	65	2026-10-12	3	\N
225	155	missing	annual_physical	65	2026-10-12	3	\N
226	156	missing	annual_physical	65	2026-10-12	3	\N
227	157	missing	annual_physical	65	2026-10-12	3	\N
228	158	missing	annual_physical	65	2026-10-12	3	\N
229	159	missing	annual_physical	65	2026-10-12	3	\N
230	160	missing	annual_physical	65	2026-10-12	3	\N
231	161	missing	annual_physical	65	2026-10-12	3	\N
232	162	missing	annual_physical	65	2026-10-12	3	\N
233	163	missing	annual_physical	65	2026-10-12	3	\N
234	164	missing	annual_physical	65	2026-10-12	3	\N
235	165	missing	annual_physical	65	2026-10-12	3	\N
236	166	missing	annual_physical	65	2026-10-12	3	\N
237	167	missing	annual_physical	65	2026-10-12	3	\N
238	168	missing	annual_physical	65	2026-10-12	3	\N
239	169	missing	annual_physical	65	2026-10-12	3	\N
240	170	missing	annual_physical	65	2026-10-12	3	\N
241	171	missing	annual_physical	65	2026-10-12	3	\N
242	172	missing	annual_physical	65	2026-10-12	3	\N
243	173	missing	annual_physical	65	2026-10-12	3	\N
244	174	missing	annual_physical	65	2026-10-12	3	\N
245	175	missing	annual_physical	65	2026-10-12	3	\N
246	176	missing	annual_physical	65	2026-10-12	3	\N
247	177	missing	annual_physical	65	2026-10-12	3	\N
248	178	missing	annual_physical	65	2026-10-12	3	\N
249	179	missing	annual_physical	65	2026-10-12	3	\N
250	180	missing	annual_physical	65	2026-10-12	3	\N
251	181	missing	annual_physical	65	2026-10-12	3	\N
252	182	missing	annual_physical	65	2026-10-12	3	\N
253	183	missing	annual_physical	65	2026-10-12	3	\N
254	184	missing	annual_physical	65	2026-10-12	3	\N
255	185	missing	annual_physical	65	2026-10-12	3	\N
256	186	missing	annual_physical	65	2026-10-12	3	\N
257	187	missing	annual_physical	65	2026-10-12	3	\N
258	188	missing	annual_physical	65	2026-10-12	3	\N
259	189	missing	annual_physical	65	2026-10-12	3	\N
260	190	missing	annual_physical	65	2026-10-12	3	\N
261	191	missing	annual_physical	65	2026-10-12	3	\N
262	192	missing	annual_physical	65	2026-10-12	3	\N
263	193	missing	annual_physical	65	2026-10-12	3	\N
264	194	missing	annual_physical	65	2026-10-12	3	\N
265	195	missing	annual_physical	65	2026-10-12	3	\N
266	196	missing	annual_physical	65	2026-10-12	3	\N
267	197	missing	annual_physical	65	2026-10-12	3	\N
268	198	missing	annual_physical	65	2026-10-12	3	\N
269	199	missing	annual_physical	65	2026-10-12	3	\N
270	200	missing	annual_physical	65	2026-10-12	3	\N
271	201	missing	annual_physical	65	2026-10-12	3	\N
272	202	missing	annual_physical	65	2026-10-12	3	\N
273	203	missing	annual_physical	65	2026-10-12	3	\N
274	204	missing	annual_physical	65	2026-10-12	3	\N
275	205	missing	annual_physical	65	2026-10-12	3	\N
276	206	missing	annual_physical	65	2026-10-12	3	\N
277	207	missing	annual_physical	65	2026-10-12	3	\N
278	208	missing	annual_physical	65	2026-10-12	3	\N
279	209	missing	annual_physical	65	2026-10-12	3	\N
280	210	missing	annual_physical	65	2026-10-12	3	\N
281	211	missing	annual_physical	65	2026-10-12	3	\N
282	212	missing	annual_physical	65	2026-10-12	3	\N
283	213	missing	annual_physical	65	2026-10-12	3	\N
284	214	missing	annual_physical	65	2026-10-12	3	\N
285	215	missing	annual_physical	65	2026-10-12	3	\N
286	216	missing	annual_physical	65	2026-10-12	3	\N
287	217	missing	annual_physical	65	2026-10-12	3	\N
288	218	missing	annual_physical	65	2026-10-12	3	\N
289	219	missing	annual_physical	65	2026-10-12	3	\N
290	220	missing	annual_physical	65	2026-10-12	3	\N
291	221	missing	annual_physical	65	2026-10-12	3	\N
292	222	missing	annual_physical	65	2026-10-12	3	\N
293	223	missing	annual_physical	65	2026-10-12	3	\N
294	224	missing	annual_physical	65	2026-10-12	3	\N
295	225	missing	annual_physical	65	2026-10-12	3	\N
296	226	missing	annual_physical	65	2026-10-12	3	\N
297	227	missing	annual_physical	65	2026-10-12	3	\N
298	228	missing	annual_physical	65	2026-10-12	3	\N
299	229	borrowed	annual_physical	65	2026-10-12	3	\N
300	230	missing	annual_physical	65	2026-10-12	3	\N
301	231	missing	annual_physical	65	2026-10-12	3	\N
302	232	missing	annual_physical	65	2026-10-12	3	\N
303	233	missing	annual_physical	65	2026-10-12	3	\N
304	234	missing	annual_physical	65	2026-10-12	3	\N
305	235	missing	annual_physical	65	2026-10-12	3	\N
306	236	missing	annual_physical	65	2026-10-12	3	\N
307	237	missing	annual_physical	65	2026-10-12	3	\N
308	238	missing	annual_physical	65	2026-10-12	3	\N
309	239	missing	annual_physical	65	2026-10-12	3	\N
310	240	missing	annual_physical	65	2026-10-12	3	\N
311	241	missing	annual_physical	65	2026-10-12	3	\N
312	242	missing	annual_physical	65	2026-10-12	3	\N
313	243	missing	annual_physical	65	2026-10-12	3	\N
314	244	missing	annual_physical	65	2026-10-12	3	\N
315	245	missing	annual_physical	65	2026-10-12	3	\N
316	246	missing	annual_physical	65	2026-10-12	3	\N
317	247	missing	annual_physical	65	2026-10-12	3	\N
318	248	missing	annual_physical	65	2026-10-12	3	\N
319	249	missing	annual_physical	65	2026-10-12	3	\N
320	250	missing	annual_physical	65	2026-10-12	3	\N
321	251	missing	annual_physical	65	2026-10-12	3	\N
322	252	missing	annual_physical	65	2026-10-12	3	\N
323	253	missing	annual_physical	65	2026-10-12	3	\N
324	254	missing	annual_physical	65	2026-10-12	3	\N
325	255	missing	annual_physical	65	2026-10-12	3	\N
326	256	missing	annual_physical	65	2026-10-12	3	\N
327	257	missing	annual_physical	65	2026-10-12	3	\N
328	258	missing	annual_physical	65	2026-10-12	3	\N
329	259	missing	annual_physical	65	2026-10-12	3	\N
330	260	missing	annual_physical	65	2026-10-12	3	\N
331	261	missing	annual_physical	65	2026-10-12	3	\N
332	262	missing	annual_physical	65	2026-10-12	3	\N
333	263	missing	annual_physical	65	2026-10-12	3	\N
334	264	missing	annual_physical	65	2026-10-12	3	\N
335	265	missing	annual_physical	65	2026-10-12	3	\N
336	266	missing	annual_physical	65	2026-10-12	3	\N
337	267	missing	annual_physical	65	2026-10-12	3	\N
338	268	missing	annual_physical	65	2026-10-12	3	\N
339	269	missing	annual_physical	65	2026-10-12	3	\N
340	270	missing	annual_physical	65	2026-10-12	3	\N
341	271	missing	annual_physical	65	2026-10-12	3	\N
342	272	missing	annual_physical	65	2026-10-12	3	\N
343	273	missing	annual_physical	65	2026-10-12	3	\N
344	274	missing	annual_physical	65	2026-10-12	3	\N
345	275	missing	annual_physical	65	2026-10-12	3	\N
346	276	missing	annual_physical	65	2026-10-12	3	\N
347	277	missing	annual_physical	65	2026-10-12	3	\N
348	278	missing	annual_physical	65	2026-10-12	3	\N
349	279	borrowed	annual_physical	65	2026-10-12	3	\N
350	280	missing	annual_physical	65	2026-10-12	3	\N
351	281	missing	annual_physical	65	2026-10-12	3	\N
352	282	missing	annual_physical	65	2026-10-12	3	\N
353	283	missing	annual_physical	65	2026-10-12	3	\N
354	284	missing	annual_physical	65	2026-10-12	3	\N
355	285	missing	annual_physical	65	2026-10-12	3	\N
356	286	missing	annual_physical	65	2026-10-12	3	\N
357	287	missing	annual_physical	65	2026-10-12	3	\N
358	288	missing	annual_physical	65	2026-10-12	3	\N
359	289	missing	annual_physical	65	2026-10-12	3	\N
360	290	missing	annual_physical	65	2026-10-12	3	\N
361	291	missing	annual_physical	65	2026-10-12	3	\N
362	292	missing	annual_physical	65	2026-10-12	3	\N
363	293	missing	annual_physical	65	2026-10-12	3	\N
364	294	missing	annual_physical	65	2026-10-12	3	\N
365	295	missing	annual_physical	65	2026-10-12	3	\N
366	296	missing	annual_physical	65	2026-10-12	3	\N
367	297	missing	annual_physical	65	2026-10-12	3	\N
368	298	missing	annual_physical	65	2026-10-12	3	\N
369	299	missing	annual_physical	65	2026-10-12	3	\N
370	300	missing	annual_physical	65	2026-10-12	3	\N
371	301	missing	annual_physical	65	2026-10-12	3	\N
372	302	missing	annual_physical	65	2026-10-12	3	\N
373	303	missing	annual_physical	65	2026-10-12	3	\N
374	304	missing	annual_physical	65	2026-10-12	3	\N
375	305	missing	annual_physical	65	2026-10-12	3	\N
376	306	missing	annual_physical	65	2026-10-12	3	\N
377	307	missing	annual_physical	65	2026-10-12	3	\N
378	308	missing	annual_physical	65	2026-10-12	3	\N
379	309	missing	annual_physical	65	2026-10-12	3	\N
380	310	missing	annual_physical	65	2026-10-12	3	\N
381	311	missing	annual_physical	65	2026-10-12	3	\N
382	312	missing	annual_physical	65	2026-10-12	3	\N
383	313	missing	annual_physical	65	2026-10-12	3	\N
384	314	missing	annual_physical	65	2026-10-12	3	\N
385	315	missing	annual_physical	65	2026-10-12	3	\N
386	316	missing	annual_physical	65	2026-10-12	3	\N
387	317	missing	annual_physical	65	2026-10-12	3	\N
388	318	missing	annual_physical	65	2026-10-12	3	\N
389	319	missing	annual_physical	65	2026-10-12	3	\N
390	320	missing	annual_physical	65	2026-10-12	3	\N
391	321	missing	annual_physical	65	2026-10-12	3	\N
392	322	missing	annual_physical	65	2026-10-12	3	\N
393	323	missing	annual_physical	65	2026-10-12	3	\N
394	324	missing	annual_physical	65	2026-10-12	3	\N
395	325	missing	annual_physical	65	2026-10-12	3	\N
396	326	missing	annual_physical	65	2026-10-12	3	\N
397	327	missing	annual_physical	65	2026-10-12	3	\N
398	328	missing	annual_physical	65	2026-10-12	3	\N
399	329	missing	annual_physical	65	2026-10-12	3	\N
400	330	missing	annual_physical	65	2026-10-12	3	\N
401	331	missing	annual_physical	65	2026-10-12	3	\N
402	332	missing	annual_physical	65	2026-10-12	3	\N
403	333	missing	annual_physical	65	2026-10-12	3	\N
404	334	missing	annual_physical	65	2026-10-12	3	\N
405	335	missing	annual_physical	65	2026-10-12	3	\N
406	336	missing	annual_physical	65	2026-10-12	3	\N
407	337	missing	annual_physical	65	2026-10-12	3	\N
408	338	missing	annual_physical	65	2026-10-12	3	\N
409	339	missing	annual_physical	65	2026-10-12	3	\N
410	340	missing	annual_physical	65	2026-10-12	3	\N
411	341	missing	annual_physical	65	2026-10-12	3	\N
412	342	missing	annual_physical	65	2026-10-12	3	\N
413	343	missing	annual_physical	65	2026-10-12	3	\N
414	344	missing	annual_physical	65	2026-10-12	3	\N
415	345	missing	annual_physical	65	2026-10-12	3	\N
416	346	missing	annual_physical	65	2026-10-12	3	\N
417	347	missing	annual_physical	65	2026-10-12	3	\N
418	348	missing	annual_physical	65	2026-10-12	3	\N
419	349	missing	annual_physical	65	2026-10-12	3	\N
420	350	missing	annual_physical	65	2026-10-12	3	\N
421	351	missing	annual_physical	65	2026-10-12	3	\N
422	352	missing	annual_physical	65	2026-10-12	3	\N
423	353	missing	annual_physical	65	2026-10-12	3	\N
424	354	missing	annual_physical	65	2026-10-12	3	\N
425	355	missing	annual_physical	65	2026-10-12	3	\N
426	356	missing	annual_physical	65	2026-10-12	3	\N
427	357	missing	annual_physical	65	2026-10-12	3	\N
428	358	missing	annual_physical	65	2026-10-12	3	\N
429	359	missing	annual_physical	65	2026-10-12	3	\N
430	360	missing	annual_physical	65	2026-10-12	3	\N
431	361	missing	annual_physical	65	2026-10-12	3	\N
432	362	missing	annual_physical	65	2026-10-12	3	\N
433	363	missing	annual_physical	65	2026-10-12	3	\N
434	364	missing	annual_physical	65	2026-10-12	3	\N
435	365	missing	annual_physical	65	2026-10-12	3	\N
436	366	missing	annual_physical	65	2026-10-12	3	\N
437	367	missing	annual_physical	65	2026-10-12	3	\N
438	368	missing	annual_physical	65	2026-10-12	3	\N
439	369	missing	annual_physical	65	2026-10-12	3	\N
440	370	missing	annual_physical	65	2026-10-12	3	\N
441	371	missing	annual_physical	65	2026-10-12	3	\N
442	372	missing	annual_physical	65	2026-10-12	3	\N
443	373	missing	annual_physical	65	2026-10-12	3	\N
444	374	missing	annual_physical	65	2026-10-12	3	\N
445	375	missing	annual_physical	65	2026-10-12	3	\N
446	376	missing	annual_physical	65	2026-10-12	3	\N
447	377	missing	annual_physical	65	2026-10-12	3	\N
448	378	missing	annual_physical	65	2026-10-12	3	\N
449	379	missing	annual_physical	65	2026-10-12	3	\N
450	380	missing	annual_physical	65	2026-10-12	3	\N
451	381	missing	annual_physical	65	2026-10-12	3	\N
452	382	missing	annual_physical	65	2026-10-12	3	\N
453	383	missing	annual_physical	65	2026-10-12	3	\N
454	384	missing	annual_physical	65	2026-10-12	3	\N
455	385	missing	annual_physical	65	2026-10-12	3	\N
456	386	missing	annual_physical	65	2026-10-12	3	\N
457	387	missing	annual_physical	65	2026-10-12	3	\N
458	388	missing	annual_physical	65	2026-10-12	3	\N
459	389	missing	annual_physical	65	2026-10-12	3	\N
460	390	missing	annual_physical	65	2026-10-12	3	\N
461	391	missing	annual_physical	65	2026-10-12	3	\N
462	392	missing	annual_physical	65	2026-10-12	3	\N
463	393	missing	annual_physical	65	2026-10-12	3	\N
464	394	missing	annual_physical	65	2026-10-12	3	\N
465	395	missing	annual_physical	65	2026-10-12	3	\N
466	396	missing	annual_physical	65	2026-10-12	3	\N
467	397	missing	annual_physical	65	2026-10-12	3	\N
468	398	missing	annual_physical	65	2026-10-12	3	\N
469	399	missing	annual_physical	65	2026-10-12	3	\N
470	400	missing	annual_physical	65	2026-10-12	3	\N
471	401	missing	annual_physical	65	2026-10-12	3	\N
472	402	missing	annual_physical	65	2026-10-12	3	\N
473	403	missing	annual_physical	65	2026-10-12	3	\N
474	404	missing	annual_physical	65	2026-10-12	3	\N
475	405	missing	annual_physical	65	2026-10-12	3	\N
476	406	missing	annual_physical	65	2026-10-12	3	\N
477	407	missing	annual_physical	65	2026-10-12	3	\N
478	408	missing	annual_physical	65	2026-10-12	3	\N
479	409	missing	annual_physical	65	2026-10-12	3	\N
480	410	missing	annual_physical	65	2026-10-12	3	\N
481	411	missing	annual_physical	65	2026-10-12	3	\N
482	412	missing	annual_physical	65	2026-10-12	3	\N
483	413	missing	annual_physical	65	2026-10-12	3	\N
484	414	missing	annual_physical	65	2026-10-12	3	\N
485	415	missing	annual_physical	65	2026-10-12	3	\N
486	416	missing	annual_physical	65	2026-10-12	3	\N
487	417	missing	annual_physical	65	2026-10-12	3	\N
488	418	missing	annual_physical	65	2026-10-12	3	\N
489	419	missing	annual_physical	65	2026-10-12	3	\N
490	420	missing	annual_physical	65	2026-10-12	3	\N
491	421	missing	annual_physical	65	2026-10-12	3	\N
492	422	missing	annual_physical	65	2026-10-12	3	\N
493	423	missing	annual_physical	65	2026-10-12	3	\N
494	424	missing	annual_physical	65	2026-10-12	3	\N
495	425	missing	annual_physical	65	2026-10-12	3	\N
496	426	missing	annual_physical	65	2026-10-12	3	\N
497	427	missing	annual_physical	65	2026-10-12	3	\N
498	428	missing	annual_physical	65	2026-10-12	3	\N
499	429	missing	annual_physical	65	2026-10-12	3	\N
500	430	missing	annual_physical	65	2026-10-12	3	\N
501	431	missing	annual_physical	65	2026-10-12	3	\N
502	432	missing	annual_physical	65	2026-10-12	3	\N
503	433	missing	annual_physical	65	2026-10-12	3	\N
504	434	missing	annual_physical	65	2026-10-12	3	\N
505	435	missing	annual_physical	65	2026-10-12	3	\N
506	436	missing	annual_physical	65	2026-10-12	3	\N
507	437	missing	annual_physical	65	2026-10-12	3	\N
508	438	missing	annual_physical	65	2026-10-12	3	\N
509	439	missing	annual_physical	65	2026-10-12	3	\N
510	440	missing	annual_physical	65	2026-10-12	3	\N
511	441	missing	annual_physical	65	2026-10-12	3	\N
512	442	missing	annual_physical	65	2026-10-12	3	\N
513	443	missing	annual_physical	65	2026-10-12	3	\N
514	444	missing	annual_physical	65	2026-10-12	3	\N
515	445	missing	annual_physical	65	2026-10-12	3	\N
516	446	missing	annual_physical	65	2026-10-12	3	\N
517	447	missing	annual_physical	65	2026-10-12	3	\N
518	448	missing	annual_physical	65	2026-10-12	3	\N
519	449	missing	annual_physical	65	2026-10-12	3	\N
520	450	missing	annual_physical	65	2026-10-12	3	\N
521	451	missing	annual_physical	65	2026-10-12	3	\N
522	452	missing	annual_physical	65	2026-10-12	3	\N
523	453	missing	annual_physical	65	2026-10-12	3	\N
524	454	missing	annual_physical	65	2026-10-12	3	\N
525	455	missing	annual_physical	65	2026-10-12	3	\N
526	456	missing	annual_physical	65	2026-10-12	3	\N
527	457	missing	annual_physical	65	2026-10-12	3	\N
528	458	missing	annual_physical	65	2026-10-12	3	\N
529	459	missing	annual_physical	65	2026-10-12	3	\N
530	460	missing	annual_physical	65	2026-10-12	3	\N
531	461	missing	annual_physical	65	2026-10-12	3	\N
532	462	missing	annual_physical	65	2026-10-12	3	\N
533	463	missing	annual_physical	65	2026-10-12	3	\N
534	464	missing	annual_physical	65	2026-10-12	3	\N
535	465	missing	annual_physical	65	2026-10-12	3	\N
536	466	missing	annual_physical	65	2026-10-12	3	\N
537	467	missing	annual_physical	65	2026-10-12	3	\N
538	468	missing	annual_physical	65	2026-10-12	3	\N
539	469	missing	annual_physical	65	2026-10-12	3	\N
540	470	missing	annual_physical	65	2026-10-12	3	\N
541	471	missing	annual_physical	65	2026-10-12	3	\N
542	472	missing	annual_physical	65	2026-10-12	3	\N
543	473	missing	annual_physical	65	2026-10-12	3	\N
544	474	missing	annual_physical	65	2026-10-12	3	\N
545	475	missing	annual_physical	65	2026-10-12	3	\N
546	476	missing	annual_physical	65	2026-10-12	3	\N
547	477	missing	annual_physical	65	2026-10-12	3	\N
548	478	missing	annual_physical	65	2026-10-12	3	\N
549	479	missing	annual_physical	65	2026-10-12	3	\N
550	480	missing	annual_physical	65	2026-10-12	3	\N
551	481	missing	annual_physical	65	2026-10-12	3	\N
552	482	missing	annual_physical	65	2026-10-12	3	\N
553	483	missing	annual_physical	65	2026-10-12	3	\N
554	484	missing	annual_physical	65	2026-10-12	3	\N
555	485	missing	annual_physical	65	2026-10-12	3	\N
556	486	missing	annual_physical	65	2026-10-12	3	\N
557	487	missing	annual_physical	65	2026-10-12	3	\N
558	488	missing	annual_physical	65	2026-10-12	3	\N
559	489	missing	annual_physical	65	2026-10-12	3	\N
560	490	missing	annual_physical	65	2026-10-12	3	\N
561	491	missing	annual_physical	65	2026-10-12	3	\N
562	492	missing	annual_physical	65	2026-10-12	3	\N
563	493	missing	annual_physical	65	2026-10-12	3	\N
564	494	missing	annual_physical	65	2026-10-12	3	\N
565	495	missing	annual_physical	65	2026-10-12	3	\N
566	496	missing	annual_physical	65	2026-10-12	3	\N
567	497	missing	annual_physical	65	2026-10-12	3	\N
568	498	missing	annual_physical	65	2026-10-12	3	\N
569	499	missing	annual_physical	65	2026-10-12	3	\N
570	500	missing	annual_physical	65	2026-10-12	3	\N
571	501	missing	annual_physical	65	2026-10-12	3	\N
572	502	missing	annual_physical	65	2026-10-12	3	\N
573	503	missing	annual_physical	65	2026-10-12	3	\N
574	504	missing	annual_physical	65	2026-10-12	3	\N
575	505	missing	annual_physical	65	2026-10-12	3	\N
576	506	missing	annual_physical	65	2026-10-12	3	\N
577	507	missing	annual_physical	65	2026-10-12	3	\N
578	508	missing	annual_physical	65	2026-10-12	3	\N
579	509	missing	annual_physical	65	2026-10-12	3	\N
580	510	missing	annual_physical	65	2026-10-12	3	\N
581	511	missing	annual_physical	65	2026-10-12	3	\N
582	512	missing	annual_physical	65	2026-10-12	3	\N
583	513	missing	annual_physical	65	2026-10-12	3	\N
584	514	missing	annual_physical	65	2026-10-12	3	\N
585	515	missing	annual_physical	65	2026-10-12	3	\N
586	516	missing	annual_physical	65	2026-10-12	3	\N
587	517	missing	annual_physical	65	2026-10-12	3	\N
588	518	missing	annual_physical	65	2026-10-12	3	\N
589	519	missing	annual_physical	65	2026-10-12	3	\N
590	520	missing	annual_physical	65	2026-10-12	3	\N
591	521	missing	annual_physical	65	2026-10-12	3	\N
592	522	missing	annual_physical	65	2026-10-12	3	\N
593	523	missing	annual_physical	65	2026-10-12	3	\N
594	524	missing	annual_physical	65	2026-10-12	3	\N
595	525	missing	annual_physical	65	2026-10-12	3	\N
596	526	missing	annual_physical	65	2026-10-12	3	\N
597	527	missing	annual_physical	65	2026-10-12	3	\N
598	528	missing	annual_physical	65	2026-10-12	3	\N
599	529	missing	annual_physical	65	2026-10-12	3	\N
600	530	missing	annual_physical	65	2026-10-12	3	\N
601	531	missing	annual_physical	65	2026-10-12	3	\N
602	532	missing	annual_physical	65	2026-10-12	3	\N
603	533	missing	annual_physical	65	2026-10-12	3	\N
604	534	missing	annual_physical	65	2026-10-12	3	\N
605	535	missing	annual_physical	65	2026-10-12	3	\N
606	536	missing	annual_physical	65	2026-10-12	3	\N
607	537	missing	annual_physical	65	2026-10-12	3	\N
608	538	missing	annual_physical	65	2026-10-12	3	\N
609	539	missing	annual_physical	65	2026-10-12	3	\N
610	540	missing	annual_physical	65	2026-10-12	3	\N
611	541	missing	annual_physical	65	2026-10-12	3	\N
612	542	missing	annual_physical	65	2026-10-12	3	\N
613	543	missing	annual_physical	65	2026-10-12	3	\N
614	544	missing	annual_physical	65	2026-10-12	3	\N
615	545	missing	annual_physical	65	2026-10-12	3	\N
616	546	missing	annual_physical	65	2026-10-12	3	\N
617	547	missing	annual_physical	65	2026-10-12	3	\N
618	548	missing	annual_physical	65	2026-10-12	3	\N
619	549	missing	annual_physical	65	2026-10-12	3	\N
620	550	missing	annual_physical	65	2026-10-12	3	\N
621	551	missing	annual_physical	65	2026-10-12	3	\N
622	552	missing	annual_physical	65	2026-10-12	3	\N
623	553	missing	annual_physical	65	2026-10-12	3	\N
624	554	missing	annual_physical	65	2026-10-12	3	\N
625	555	missing	annual_physical	65	2026-10-12	3	\N
626	556	missing	annual_physical	65	2026-10-12	3	\N
627	557	missing	annual_physical	65	2026-10-12	3	\N
628	558	missing	annual_physical	65	2026-10-12	3	\N
629	559	missing	annual_physical	65	2026-10-12	3	\N
630	560	missing	annual_physical	65	2026-10-12	3	\N
631	561	missing	annual_physical	65	2026-10-12	3	\N
632	562	missing	annual_physical	65	2026-10-12	3	\N
633	563	missing	annual_physical	65	2026-10-12	3	\N
634	564	missing	annual_physical	65	2026-10-12	3	\N
635	565	missing	annual_physical	65	2026-10-12	3	\N
636	566	missing	annual_physical	65	2026-10-12	3	\N
637	567	missing	annual_physical	65	2026-10-12	3	\N
638	568	missing	annual_physical	65	2026-10-12	3	\N
639	569	missing	annual_physical	65	2026-10-12	3	\N
640	570	missing	annual_physical	65	2026-10-12	3	\N
641	571	missing	annual_physical	65	2026-10-12	3	\N
642	572	missing	annual_physical	65	2026-10-12	3	\N
643	573	missing	annual_physical	65	2026-10-12	3	\N
644	574	missing	annual_physical	65	2026-10-12	3	\N
645	575	missing	annual_physical	65	2026-10-12	3	\N
646	576	missing	annual_physical	65	2026-10-12	3	\N
647	577	missing	annual_physical	65	2026-10-12	3	\N
648	578	missing	annual_physical	65	2026-10-12	3	\N
649	579	missing	annual_physical	65	2026-10-12	3	\N
650	580	missing	annual_physical	65	2026-10-12	3	\N
651	581	missing	annual_physical	65	2026-10-12	3	\N
652	582	missing	annual_physical	65	2026-10-12	3	\N
653	583	missing	annual_physical	65	2026-10-12	3	\N
654	584	missing	annual_physical	65	2026-10-12	3	\N
655	585	missing	annual_physical	65	2026-10-12	3	\N
656	586	missing	annual_physical	65	2026-10-12	3	\N
657	587	missing	annual_physical	65	2026-10-12	3	\N
658	588	missing	annual_physical	65	2026-10-12	3	\N
659	589	missing	annual_physical	65	2026-10-12	3	\N
660	590	missing	annual_physical	65	2026-10-12	3	\N
661	591	missing	annual_physical	65	2026-10-12	3	\N
662	592	missing	annual_physical	65	2026-10-12	3	\N
663	593	missing	annual_physical	65	2026-10-12	3	\N
664	594	missing	annual_physical	65	2026-10-12	3	\N
665	595	missing	annual_physical	65	2026-10-12	3	\N
666	596	missing	annual_physical	65	2026-10-12	3	\N
667	597	missing	annual_physical	65	2026-10-12	3	\N
668	598	missing	annual_physical	65	2026-10-12	3	\N
669	599	missing	annual_physical	65	2026-10-12	3	\N
670	600	missing	annual_physical	65	2026-10-12	3	\N
671	601	missing	annual_physical	65	2026-10-12	3	\N
672	602	missing	annual_physical	65	2026-10-12	3	\N
673	603	missing	annual_physical	65	2026-10-12	3	\N
674	604	missing	annual_physical	65	2026-10-12	3	\N
675	605	missing	annual_physical	65	2026-10-12	3	\N
676	606	missing	annual_physical	65	2026-10-12	3	\N
677	607	missing	annual_physical	65	2026-10-12	3	\N
678	608	missing	annual_physical	65	2026-10-12	3	\N
679	609	missing	annual_physical	65	2026-10-12	3	\N
680	610	missing	annual_physical	65	2026-10-12	3	\N
681	611	missing	annual_physical	65	2026-10-12	3	\N
682	612	missing	annual_physical	65	2026-10-12	3	\N
683	613	missing	annual_physical	65	2026-10-12	3	\N
684	614	missing	annual_physical	65	2026-10-12	3	\N
685	615	missing	annual_physical	65	2026-10-12	3	\N
686	616	missing	annual_physical	65	2026-10-12	3	\N
687	617	missing	annual_physical	65	2026-10-12	3	\N
688	618	missing	annual_physical	65	2026-10-12	3	\N
689	619	missing	annual_physical	65	2026-10-12	3	\N
690	620	missing	annual_physical	65	2026-10-12	3	\N
691	621	missing	annual_physical	65	2026-10-12	3	\N
692	622	missing	annual_physical	65	2026-10-12	3	\N
693	623	missing	annual_physical	65	2026-10-12	3	\N
694	624	missing	annual_physical	65	2026-10-12	3	\N
695	625	missing	annual_physical	65	2026-10-12	3	\N
696	626	missing	annual_physical	65	2026-10-12	3	\N
697	627	missing	annual_physical	65	2026-10-12	3	\N
698	628	missing	annual_physical	65	2026-10-12	3	\N
699	629	borrowed	annual_physical	65	2026-10-12	3	\N
700	630	missing	annual_physical	65	2026-10-12	3	\N
701	631	missing	annual_physical	65	2026-10-12	3	\N
702	632	missing	annual_physical	65	2026-10-12	3	\N
703	633	missing	annual_physical	65	2026-10-12	3	\N
704	634	missing	annual_physical	65	2026-10-12	3	\N
705	635	missing	annual_physical	65	2026-10-12	3	\N
706	636	missing	annual_physical	65	2026-10-12	3	\N
707	637	missing	annual_physical	65	2026-10-12	3	\N
708	638	missing	annual_physical	65	2026-10-12	3	\N
709	639	missing	annual_physical	65	2026-10-12	3	\N
710	640	missing	annual_physical	65	2026-10-12	3	\N
711	641	missing	annual_physical	65	2026-10-12	3	\N
712	642	missing	annual_physical	65	2026-10-12	3	\N
713	643	missing	annual_physical	65	2026-10-12	3	\N
714	644	missing	annual_physical	65	2026-10-12	3	\N
715	645	missing	annual_physical	65	2026-10-12	3	\N
716	646	missing	annual_physical	65	2026-10-12	3	\N
717	647	missing	annual_physical	65	2026-10-12	3	\N
718	648	missing	annual_physical	65	2026-10-12	3	\N
719	649	missing	annual_physical	65	2026-10-12	3	\N
720	650	missing	annual_physical	65	2026-10-12	3	\N
721	651	missing	annual_physical	65	2026-10-12	3	\N
722	652	missing	annual_physical	65	2026-10-12	3	\N
723	653	missing	annual_physical	65	2026-10-12	3	\N
724	654	missing	annual_physical	65	2026-10-12	3	\N
725	655	missing	annual_physical	65	2026-10-12	3	\N
726	656	missing	annual_physical	65	2026-10-12	3	\N
727	657	missing	annual_physical	65	2026-10-12	3	\N
728	658	missing	annual_physical	65	2026-10-12	3	\N
729	659	missing	annual_physical	65	2026-10-12	3	\N
730	660	missing	annual_physical	65	2026-10-12	3	\N
731	661	missing	annual_physical	65	2026-10-12	3	\N
732	662	missing	annual_physical	65	2026-10-12	3	\N
733	663	missing	annual_physical	65	2026-10-12	3	\N
734	664	missing	annual_physical	65	2026-10-12	3	\N
735	665	missing	annual_physical	65	2026-10-12	3	\N
736	666	missing	annual_physical	65	2026-10-12	3	\N
737	667	missing	annual_physical	65	2026-10-12	3	\N
738	668	missing	annual_physical	65	2026-10-12	3	\N
739	669	missing	annual_physical	65	2026-10-12	3	\N
740	670	missing	annual_physical	65	2026-10-12	3	\N
741	671	missing	annual_physical	65	2026-10-12	3	\N
742	672	missing	annual_physical	65	2026-10-12	3	\N
743	673	missing	annual_physical	65	2026-10-12	3	\N
744	674	missing	annual_physical	65	2026-10-12	3	\N
745	675	missing	annual_physical	65	2026-10-12	3	\N
746	676	missing	annual_physical	65	2026-10-12	3	\N
747	677	missing	annual_physical	65	2026-10-12	3	\N
748	678	missing	annual_physical	65	2026-10-12	3	\N
749	679	missing	annual_physical	65	2026-10-12	3	\N
750	680	missing	annual_physical	65	2026-10-12	3	\N
751	681	missing	annual_physical	65	2026-10-12	3	\N
752	682	missing	annual_physical	65	2026-10-12	3	\N
753	683	missing	annual_physical	65	2026-10-12	3	\N
754	684	missing	annual_physical	65	2026-10-12	3	\N
755	685	missing	annual_physical	65	2026-10-12	3	\N
756	686	missing	annual_physical	65	2026-10-12	3	\N
757	687	missing	annual_physical	65	2026-10-12	3	\N
758	688	missing	annual_physical	65	2026-10-12	3	\N
759	689	missing	annual_physical	65	2026-10-12	3	\N
760	690	missing	annual_physical	65	2026-10-12	3	\N
761	691	missing	annual_physical	65	2026-10-12	3	\N
762	692	missing	annual_physical	65	2026-10-12	3	\N
763	693	missing	annual_physical	65	2026-10-12	3	\N
764	694	missing	annual_physical	65	2026-10-12	3	\N
765	695	missing	annual_physical	65	2026-10-12	3	\N
766	696	missing	annual_physical	65	2026-10-12	3	\N
767	697	missing	annual_physical	65	2026-10-12	3	\N
768	698	missing	annual_physical	65	2026-10-12	3	\N
769	699	missing	annual_physical	65	2026-10-12	3	\N
770	700	missing	annual_physical	65	2026-10-12	3	\N
771	701	missing	annual_physical	65	2026-10-12	3	\N
772	702	missing	annual_physical	65	2026-10-12	3	\N
773	703	missing	annual_physical	65	2026-10-12	3	\N
774	704	missing	annual_physical	65	2026-10-12	3	\N
775	705	missing	annual_physical	65	2026-10-12	3	\N
776	706	missing	annual_physical	65	2026-10-12	3	\N
777	707	missing	annual_physical	65	2026-10-12	3	\N
778	708	missing	annual_physical	65	2026-10-12	3	\N
779	709	missing	annual_physical	65	2026-10-12	3	\N
780	710	missing	annual_physical	65	2026-10-12	3	\N
781	711	missing	annual_physical	65	2026-10-12	3	\N
782	712	missing	annual_physical	65	2026-10-12	3	\N
783	713	missing	annual_physical	65	2026-10-12	3	\N
784	714	missing	annual_physical	65	2026-10-12	3	\N
785	715	missing	annual_physical	65	2026-10-12	3	\N
786	716	missing	annual_physical	65	2026-10-12	3	\N
787	717	missing	annual_physical	65	2026-10-12	3	\N
788	718	missing	annual_physical	65	2026-10-12	3	\N
789	719	missing	annual_physical	65	2026-10-12	3	\N
790	720	missing	annual_physical	65	2026-10-12	3	\N
791	721	missing	annual_physical	65	2026-10-12	3	\N
792	722	missing	annual_physical	65	2026-10-12	3	\N
793	723	missing	annual_physical	65	2026-10-12	3	\N
794	724	missing	annual_physical	65	2026-10-12	3	\N
795	725	missing	annual_physical	65	2026-10-12	3	\N
796	726	missing	annual_physical	65	2026-10-12	3	\N
797	727	missing	annual_physical	65	2026-10-12	3	\N
798	728	missing	annual_physical	65	2026-10-12	3	\N
799	729	missing	annual_physical	65	2026-10-12	3	\N
800	730	missing	annual_physical	65	2026-10-12	3	\N
801	731	missing	annual_physical	65	2026-10-12	3	\N
802	732	missing	annual_physical	65	2026-10-12	3	\N
803	733	missing	annual_physical	65	2026-10-12	3	\N
804	734	missing	annual_physical	65	2026-10-12	3	\N
805	735	missing	annual_physical	65	2026-10-12	3	\N
806	736	missing	annual_physical	65	2026-10-12	3	\N
807	737	missing	annual_physical	65	2026-10-12	3	\N
808	738	missing	annual_physical	65	2026-10-12	3	\N
809	739	missing	annual_physical	65	2026-10-12	3	\N
810	740	missing	annual_physical	65	2026-10-12	3	\N
811	741	missing	annual_physical	65	2026-10-12	3	\N
812	742	missing	annual_physical	65	2026-10-12	3	\N
813	743	missing	annual_physical	65	2026-10-12	3	\N
814	744	missing	annual_physical	65	2026-10-12	3	\N
815	745	missing	annual_physical	65	2026-10-12	3	\N
816	746	missing	annual_physical	65	2026-10-12	3	\N
817	747	missing	annual_physical	65	2026-10-12	3	\N
818	748	missing	annual_physical	65	2026-10-12	3	\N
819	749	missing	annual_physical	65	2026-10-12	3	\N
820	750	missing	annual_physical	65	2026-10-12	3	\N
821	751	missing	annual_physical	65	2026-10-12	3	\N
822	752	missing	annual_physical	65	2026-10-12	3	\N
823	753	missing	annual_physical	65	2026-10-12	3	\N
824	754	missing	annual_physical	65	2026-10-12	3	\N
825	755	missing	annual_physical	65	2026-10-12	3	\N
826	756	missing	annual_physical	65	2026-10-12	3	\N
827	757	missing	annual_physical	65	2026-10-12	3	\N
828	758	missing	annual_physical	65	2026-10-12	3	\N
829	759	missing	annual_physical	65	2026-10-12	3	\N
830	760	missing	annual_physical	65	2026-10-12	3	\N
831	761	missing	annual_physical	65	2026-10-12	3	\N
832	762	missing	annual_physical	65	2026-10-12	3	\N
833	763	missing	annual_physical	65	2026-10-12	3	\N
834	764	missing	annual_physical	65	2026-10-12	3	\N
835	765	missing	annual_physical	65	2026-10-12	3	\N
836	766	missing	annual_physical	65	2026-10-12	3	\N
837	767	missing	annual_physical	65	2026-10-12	3	\N
838	768	missing	annual_physical	65	2026-10-12	3	\N
839	769	missing	annual_physical	65	2026-10-12	3	\N
840	770	missing	annual_physical	65	2026-10-12	3	\N
841	771	missing	annual_physical	65	2026-10-12	3	\N
842	772	missing	annual_physical	65	2026-10-12	3	\N
843	773	missing	annual_physical	65	2026-10-12	3	\N
844	774	missing	annual_physical	65	2026-10-12	3	\N
845	775	missing	annual_physical	65	2026-10-12	3	\N
846	776	missing	annual_physical	65	2026-10-12	3	\N
847	777	missing	annual_physical	65	2026-10-12	3	\N
848	778	missing	annual_physical	65	2026-10-12	3	\N
849	779	missing	annual_physical	65	2026-10-12	3	\N
850	780	missing	annual_physical	65	2026-10-12	3	\N
851	781	missing	annual_physical	65	2026-10-12	3	\N
852	782	missing	annual_physical	65	2026-10-12	3	\N
853	783	missing	annual_physical	65	2026-10-12	3	\N
854	784	missing	annual_physical	65	2026-10-12	3	\N
855	785	missing	annual_physical	65	2026-10-12	3	\N
856	786	missing	annual_physical	65	2026-10-12	3	\N
857	787	missing	annual_physical	65	2026-10-12	3	\N
858	788	missing	annual_physical	65	2026-10-12	3	\N
859	789	missing	annual_physical	65	2026-10-12	3	\N
860	790	missing	annual_physical	65	2026-10-12	3	\N
861	791	missing	annual_physical	65	2026-10-12	3	\N
862	792	missing	annual_physical	65	2026-10-12	3	\N
863	793	missing	annual_physical	65	2026-10-12	3	\N
864	794	missing	annual_physical	65	2026-10-12	3	\N
865	795	missing	annual_physical	65	2026-10-12	3	\N
866	796	missing	annual_physical	65	2026-10-12	3	\N
867	797	missing	annual_physical	65	2026-10-12	3	\N
868	798	missing	annual_physical	65	2026-10-12	3	\N
869	799	missing	annual_physical	65	2026-10-12	3	\N
870	800	missing	annual_physical	65	2026-10-12	3	\N
871	801	missing	annual_physical	65	2026-10-12	3	\N
872	802	missing	annual_physical	65	2026-10-12	3	\N
873	803	missing	annual_physical	65	2026-10-12	3	\N
874	804	missing	annual_physical	65	2026-10-12	3	\N
875	805	missing	annual_physical	65	2026-10-12	3	\N
876	806	missing	annual_physical	65	2026-10-12	3	\N
877	807	missing	annual_physical	65	2026-10-12	3	\N
878	808	missing	annual_physical	65	2026-10-12	3	\N
879	809	missing	annual_physical	65	2026-10-12	3	\N
880	810	missing	annual_physical	65	2026-10-12	3	\N
881	811	missing	annual_physical	65	2026-10-12	3	\N
882	812	missing	annual_physical	65	2026-10-12	3	\N
883	813	missing	annual_physical	65	2026-10-12	3	\N
884	814	missing	annual_physical	65	2026-10-12	3	\N
885	815	missing	annual_physical	65	2026-10-12	3	\N
886	816	missing	annual_physical	65	2026-10-12	3	\N
887	817	missing	annual_physical	65	2026-10-12	3	\N
888	818	missing	annual_physical	65	2026-10-12	3	\N
889	819	missing	annual_physical	65	2026-10-12	3	\N
890	820	missing	annual_physical	65	2026-10-12	3	\N
891	821	missing	annual_physical	65	2026-10-12	3	\N
892	822	missing	annual_physical	65	2026-10-12	3	\N
893	823	missing	annual_physical	65	2026-10-12	3	\N
894	824	missing	annual_physical	65	2026-10-12	3	\N
895	825	missing	annual_physical	65	2026-10-12	3	\N
896	826	missing	annual_physical	65	2026-10-12	3	\N
897	827	missing	annual_physical	65	2026-10-12	3	\N
898	828	missing	annual_physical	65	2026-10-12	3	\N
899	829	missing	annual_physical	65	2026-10-12	3	\N
900	830	missing	annual_physical	65	2026-10-12	3	\N
901	831	missing	annual_physical	65	2026-10-12	3	\N
902	832	missing	annual_physical	65	2026-10-12	3	\N
903	833	missing	annual_physical	65	2026-10-12	3	\N
904	834	missing	annual_physical	65	2026-10-12	3	\N
905	835	missing	annual_physical	65	2026-10-12	3	\N
906	836	missing	annual_physical	65	2026-10-12	3	\N
907	837	missing	annual_physical	65	2026-10-12	3	\N
908	838	missing	annual_physical	65	2026-10-12	3	\N
909	839	missing	annual_physical	65	2026-10-12	3	\N
910	840	missing	annual_physical	65	2026-10-12	3	\N
911	841	missing	annual_physical	65	2026-10-12	3	\N
912	842	missing	annual_physical	65	2026-10-12	3	\N
913	843	missing	annual_physical	65	2026-10-12	3	\N
914	844	missing	annual_physical	65	2026-10-12	3	\N
915	845	missing	annual_physical	65	2026-10-12	3	\N
916	846	missing	annual_physical	65	2026-10-12	3	\N
917	847	missing	annual_physical	65	2026-10-12	3	\N
918	848	missing	annual_physical	65	2026-10-12	3	\N
919	849	missing	annual_physical	65	2026-10-12	3	\N
920	850	missing	annual_physical	65	2026-10-12	3	\N
921	851	missing	annual_physical	65	2026-10-12	3	\N
922	852	missing	annual_physical	65	2026-10-12	3	\N
923	853	missing	annual_physical	65	2026-10-12	3	\N
924	854	missing	annual_physical	65	2026-10-12	3	\N
925	855	missing	annual_physical	65	2026-10-12	3	\N
926	856	missing	annual_physical	65	2026-10-12	3	\N
927	857	missing	annual_physical	65	2026-10-12	3	\N
928	858	missing	annual_physical	65	2026-10-12	3	\N
929	859	missing	annual_physical	65	2026-10-12	3	\N
930	860	missing	annual_physical	65	2026-10-12	3	\N
931	861	missing	annual_physical	65	2026-10-12	3	\N
932	862	missing	annual_physical	65	2026-10-12	3	\N
933	863	missing	annual_physical	65	2026-10-12	3	\N
934	864	missing	annual_physical	65	2026-10-12	3	\N
935	865	missing	annual_physical	65	2026-10-12	3	\N
936	866	missing	annual_physical	65	2026-10-12	3	\N
937	867	missing	annual_physical	65	2026-10-12	3	\N
938	868	missing	annual_physical	65	2026-10-12	3	\N
939	869	missing	annual_physical	65	2026-10-12	3	\N
940	870	missing	annual_physical	65	2026-10-12	3	\N
941	871	missing	annual_physical	65	2026-10-12	3	\N
942	872	missing	annual_physical	65	2026-10-12	3	\N
943	873	missing	annual_physical	65	2026-10-12	3	\N
944	874	missing	annual_physical	65	2026-10-12	3	\N
945	875	missing	annual_physical	65	2026-10-12	3	\N
946	876	missing	annual_physical	65	2026-10-12	3	\N
947	877	missing	annual_physical	65	2026-10-12	3	\N
948	878	missing	annual_physical	65	2026-10-12	3	\N
949	879	missing	annual_physical	65	2026-10-12	3	\N
950	880	missing	annual_physical	65	2026-10-12	3	\N
951	881	missing	annual_physical	65	2026-10-12	3	\N
952	882	missing	annual_physical	65	2026-10-12	3	\N
953	883	missing	annual_physical	65	2026-10-12	3	\N
954	884	missing	annual_physical	65	2026-10-12	3	\N
955	885	missing	annual_physical	65	2026-10-12	3	\N
956	886	missing	annual_physical	65	2026-10-12	3	\N
957	887	missing	annual_physical	65	2026-10-12	3	\N
958	888	missing	annual_physical	65	2026-10-12	3	\N
959	889	missing	annual_physical	65	2026-10-12	3	\N
960	890	missing	annual_physical	65	2026-10-12	3	\N
961	891	missing	annual_physical	65	2026-10-12	3	\N
962	892	missing	annual_physical	65	2026-10-12	3	\N
963	893	missing	annual_physical	65	2026-10-12	3	\N
964	894	missing	annual_physical	65	2026-10-12	3	\N
965	895	missing	annual_physical	65	2026-10-12	3	\N
966	896	missing	annual_physical	65	2026-10-12	3	\N
967	897	missing	annual_physical	65	2026-10-12	3	\N
968	898	missing	annual_physical	65	2026-10-12	3	\N
969	899	missing	annual_physical	65	2026-10-12	3	\N
970	900	missing	annual_physical	65	2026-10-12	3	\N
971	901	borrowed	annual_physical	65	2026-10-12	3	\N
972	902	missing	annual_physical	65	2026-10-12	3	\N
973	903	missing	annual_physical	65	2026-10-12	3	\N
974	904	missing	annual_physical	65	2026-10-12	3	\N
975	905	missing	annual_physical	65	2026-10-12	3	\N
976	906	missing	annual_physical	65	2026-10-12	3	\N
977	907	missing	annual_physical	65	2026-10-12	3	\N
978	908	missing	annual_physical	65	2026-10-12	3	\N
979	909	missing	annual_physical	65	2026-10-12	3	\N
980	910	missing	annual_physical	65	2026-10-12	3	\N
981	911	missing	annual_physical	65	2026-10-12	3	\N
982	912	missing	annual_physical	65	2026-10-12	3	\N
983	913	missing	annual_physical	65	2026-10-12	3	\N
984	914	missing	annual_physical	65	2026-10-12	3	\N
985	915	missing	annual_physical	65	2026-10-12	3	\N
986	916	missing	annual_physical	65	2026-10-12	3	\N
987	917	missing	annual_physical	65	2026-10-12	3	\N
988	918	missing	annual_physical	65	2026-10-12	3	\N
989	919	missing	annual_physical	65	2026-10-12	3	\N
990	920	missing	annual_physical	65	2026-10-12	3	\N
991	921	missing	annual_physical	65	2026-10-12	3	\N
992	922	missing	annual_physical	65	2026-10-12	3	\N
993	923	missing	annual_physical	65	2026-10-12	3	\N
994	924	missing	annual_physical	65	2026-10-12	3	\N
995	925	missing	annual_physical	65	2026-10-12	3	\N
996	926	missing	annual_physical	65	2026-10-12	3	\N
997	927	missing	annual_physical	65	2026-10-12	3	\N
998	928	missing	annual_physical	65	2026-10-12	3	\N
999	929	missing	annual_physical	65	2026-10-12	3	\N
1000	930	missing	annual_physical	65	2026-10-12	3	\N
1001	931	missing	annual_physical	65	2026-10-12	3	\N
1002	932	missing	annual_physical	65	2026-10-12	3	\N
1003	933	missing	annual_physical	65	2026-10-12	3	\N
1004	934	missing	annual_physical	65	2026-10-12	3	\N
1005	935	missing	annual_physical	65	2026-10-12	3	\N
1006	936	missing	annual_physical	65	2026-10-12	3	\N
1007	937	missing	annual_physical	65	2026-10-12	3	\N
1008	938	missing	annual_physical	65	2026-10-12	3	\N
1009	939	missing	annual_physical	65	2026-10-12	3	\N
1010	940	missing	annual_physical	65	2026-10-12	3	\N
1011	941	missing	annual_physical	65	2026-10-12	3	\N
1012	942	missing	annual_physical	65	2026-10-12	3	\N
1013	943	missing	annual_physical	65	2026-10-12	3	\N
1014	944	missing	annual_physical	65	2026-10-12	3	\N
1015	945	missing	annual_physical	65	2026-10-12	3	\N
1016	946	missing	annual_physical	65	2026-10-12	3	\N
1017	947	missing	annual_physical	65	2026-10-12	3	\N
1018	948	missing	annual_physical	65	2026-10-12	3	\N
1019	949	missing	annual_physical	65	2026-10-12	3	\N
1020	950	missing	annual_physical	65	2026-10-12	3	\N
1021	951	missing	annual_physical	65	2026-10-12	3	\N
1022	952	missing	annual_physical	65	2026-10-12	3	\N
1023	953	missing	annual_physical	65	2026-10-12	3	\N
1024	954	missing	annual_physical	65	2026-10-12	3	\N
1025	955	missing	annual_physical	65	2026-10-12	3	\N
1026	956	missing	annual_physical	65	2026-10-12	3	\N
1027	957	missing	annual_physical	65	2026-10-12	3	\N
1028	958	missing	annual_physical	65	2026-10-12	3	\N
1029	959	missing	annual_physical	65	2026-10-12	3	\N
1030	960	missing	annual_physical	65	2026-10-12	3	\N
1031	961	missing	annual_physical	65	2026-10-12	3	\N
1032	962	missing	annual_physical	65	2026-10-12	3	\N
1033	963	missing	annual_physical	65	2026-10-12	3	\N
1034	964	missing	annual_physical	65	2026-10-12	3	\N
1035	965	missing	annual_physical	65	2026-10-12	3	\N
1036	966	missing	annual_physical	65	2026-10-12	3	\N
1037	967	missing	annual_physical	65	2026-10-12	3	\N
1038	968	missing	annual_physical	65	2026-10-12	3	\N
1039	969	missing	annual_physical	65	2026-10-12	3	\N
1040	970	missing	annual_physical	65	2026-10-12	3	\N
1041	971	missing	annual_physical	65	2026-10-12	3	\N
1042	972	missing	annual_physical	65	2026-10-12	3	\N
1043	973	missing	annual_physical	65	2026-10-12	3	\N
1044	974	missing	annual_physical	65	2026-10-12	3	\N
1045	975	missing	annual_physical	65	2026-10-12	3	\N
1046	976	missing	annual_physical	65	2026-10-12	3	\N
1047	977	missing	annual_physical	65	2026-10-12	3	\N
1048	978	missing	annual_physical	65	2026-10-12	3	\N
1049	979	missing	annual_physical	65	2026-10-12	3	\N
1050	980	missing	annual_physical	65	2026-10-12	3	\N
1051	981	missing	annual_physical	65	2026-10-12	3	\N
1052	982	missing	annual_physical	65	2026-10-12	3	\N
1053	983	missing	annual_physical	65	2026-10-12	3	\N
1054	984	missing	annual_physical	65	2026-10-12	3	\N
1055	985	missing	annual_physical	65	2026-10-12	3	\N
1056	986	missing	annual_physical	65	2026-10-12	3	\N
1057	987	missing	annual_physical	65	2026-10-12	3	\N
1058	988	missing	annual_physical	65	2026-10-12	3	\N
1059	989	missing	annual_physical	65	2026-10-12	3	\N
1060	990	missing	annual_physical	65	2026-10-12	3	\N
1061	991	missing	annual_physical	65	2026-10-12	3	\N
1062	992	missing	annual_physical	65	2026-10-12	3	\N
1063	993	missing	annual_physical	65	2026-10-12	3	\N
1064	994	missing	annual_physical	65	2026-10-12	3	\N
1065	995	missing	annual_physical	65	2026-10-12	3	\N
1066	996	missing	annual_physical	65	2026-10-12	3	\N
1067	997	missing	annual_physical	65	2026-10-12	3	\N
1068	998	missing	annual_physical	65	2026-10-12	3	\N
1069	999	missing	annual_physical	65	2026-10-12	3	\N
1070	1000	missing	annual_physical	65	2026-10-12	3	\N
1071	1001	missing	annual_physical	65	2026-10-12	3	\N
1072	1002	missing	annual_physical	65	2026-10-12	3	\N
1073	1003	missing	annual_physical	65	2026-10-12	3	\N
1074	1004	missing	annual_physical	65	2026-10-12	3	\N
1075	1005	missing	annual_physical	65	2026-10-12	3	\N
1076	1006	missing	annual_physical	65	2026-10-12	3	\N
1077	1007	missing	annual_physical	65	2026-10-12	3	\N
1078	1008	missing	annual_physical	65	2026-10-12	3	\N
1079	1009	missing	annual_physical	65	2026-10-12	3	\N
1080	1010	missing	annual_physical	65	2026-10-12	3	\N
1081	1011	missing	annual_physical	65	2026-10-12	3	\N
1082	1012	missing	annual_physical	65	2026-10-12	3	\N
1083	1013	missing	annual_physical	65	2026-10-12	3	\N
1084	1014	missing	annual_physical	65	2026-10-12	3	\N
1085	1015	missing	annual_physical	65	2026-10-12	3	\N
1086	1016	missing	annual_physical	65	2026-10-12	3	\N
1087	1017	missing	annual_physical	65	2026-10-12	3	\N
1088	1018	missing	annual_physical	65	2026-10-12	3	\N
1089	1019	missing	annual_physical	65	2026-10-12	3	\N
1090	1020	missing	annual_physical	65	2026-10-12	3	\N
1091	1021	missing	annual_physical	65	2026-10-12	3	\N
1092	1022	missing	annual_physical	65	2026-10-12	3	\N
1093	1023	missing	annual_physical	65	2026-10-12	3	\N
1094	1024	missing	annual_physical	65	2026-10-12	3	\N
1095	1025	missing	annual_physical	65	2026-10-12	3	\N
1096	1026	missing	annual_physical	65	2026-10-12	3	\N
1097	1027	missing	annual_physical	65	2026-10-12	3	\N
1098	1028	missing	annual_physical	65	2026-10-12	3	\N
1099	1029	missing	annual_physical	65	2026-10-12	3	\N
1100	1030	missing	annual_physical	65	2026-10-12	3	\N
1101	1031	missing	annual_physical	65	2026-10-12	3	\N
1102	1032	missing	annual_physical	65	2026-10-12	3	\N
1103	1033	missing	annual_physical	65	2026-10-12	3	\N
1104	1034	missing	annual_physical	65	2026-10-12	3	\N
1105	1035	missing	annual_physical	65	2026-10-12	3	\N
1106	1036	missing	annual_physical	65	2026-10-12	3	\N
1107	1037	missing	annual_physical	65	2026-10-12	3	\N
1108	1038	missing	annual_physical	65	2026-10-12	3	\N
1109	1039	missing	annual_physical	65	2026-10-12	3	\N
1110	1040	missing	annual_physical	65	2026-10-12	3	\N
1111	1041	missing	annual_physical	65	2026-10-12	3	\N
1112	1042	missing	annual_physical	65	2026-10-12	3	\N
1113	1043	missing	annual_physical	65	2026-10-12	3	\N
1114	1044	missing	annual_physical	65	2026-10-12	3	\N
1115	1045	missing	annual_physical	65	2026-10-12	3	\N
1116	1046	missing	annual_physical	65	2026-10-12	3	\N
1117	1047	missing	annual_physical	65	2026-10-12	3	\N
1118	1048	missing	annual_physical	65	2026-10-12	3	\N
1119	1049	missing	annual_physical	65	2026-10-12	3	\N
1120	1050	missing	annual_physical	65	2026-10-12	3	\N
1121	1051	missing	annual_physical	65	2026-10-12	3	\N
1122	1052	missing	annual_physical	65	2026-10-12	3	\N
1123	1053	missing	annual_physical	65	2026-10-12	3	\N
1124	1054	missing	annual_physical	65	2026-10-12	3	\N
1125	1055	missing	annual_physical	65	2026-10-12	3	\N
1126	1056	missing	annual_physical	65	2026-10-12	3	\N
1127	1057	missing	annual_physical	65	2026-10-12	3	\N
1128	1058	missing	annual_physical	65	2026-10-12	3	\N
1129	1059	missing	annual_physical	65	2026-10-12	3	\N
1130	1060	missing	annual_physical	65	2026-10-12	3	\N
1131	1061	missing	annual_physical	65	2026-10-12	3	\N
1132	1062	missing	annual_physical	65	2026-10-12	3	\N
1133	1063	missing	annual_physical	65	2026-10-12	3	\N
1134	1064	missing	annual_physical	65	2026-10-12	3	\N
1135	1065	missing	annual_physical	65	2026-10-12	3	\N
1136	1066	missing	annual_physical	65	2026-10-12	3	\N
1137	1067	missing	annual_physical	65	2026-10-12	3	\N
1138	1068	missing	annual_physical	65	2026-10-12	3	\N
1139	1069	missing	annual_physical	65	2026-10-12	3	\N
1140	1070	missing	annual_physical	65	2026-10-12	3	\N
1141	1071	missing	annual_physical	65	2026-10-12	3	\N
1142	1072	missing	annual_physical	65	2026-10-12	3	\N
1143	1073	missing	annual_physical	65	2026-10-12	3	\N
1144	1074	missing	annual_physical	65	2026-10-12	3	\N
1145	1075	missing	annual_physical	65	2026-10-12	3	\N
1146	1076	missing	annual_physical	65	2026-10-12	3	\N
1147	1077	missing	annual_physical	65	2026-10-12	3	\N
1148	1078	missing	annual_physical	65	2026-10-12	3	\N
1149	1079	missing	annual_physical	65	2026-10-12	3	\N
1150	1080	missing	annual_physical	65	2026-10-12	3	\N
1151	1081	missing	annual_physical	65	2026-10-12	3	\N
1152	1082	missing	annual_physical	65	2026-10-12	3	\N
1153	1083	missing	annual_physical	65	2026-10-12	3	\N
1154	1084	missing	annual_physical	65	2026-10-12	3	\N
1155	1085	missing	annual_physical	65	2026-10-12	3	\N
1156	1086	missing	annual_physical	65	2026-10-12	3	\N
1157	1087	missing	annual_physical	65	2026-10-12	3	\N
1158	1088	missing	annual_physical	65	2026-10-12	3	\N
1159	1089	missing	annual_physical	65	2026-10-12	3	\N
1160	1090	missing	annual_physical	65	2026-10-12	3	\N
1161	1091	missing	annual_physical	65	2026-10-12	3	\N
1162	1092	missing	annual_physical	65	2026-10-12	3	\N
1163	1093	missing	annual_physical	65	2026-10-12	3	\N
1164	1094	missing	annual_physical	65	2026-10-12	3	\N
1165	1095	missing	annual_physical	65	2026-10-12	3	\N
1166	1096	missing	annual_physical	65	2026-10-12	3	\N
1167	1097	missing	annual_physical	65	2026-10-12	3	\N
1168	1098	missing	annual_physical	65	2026-10-12	3	\N
1169	1099	missing	annual_physical	65	2026-10-12	3	\N
1170	1100	missing	annual_physical	65	2026-10-12	3	\N
1171	1101	missing	annual_physical	65	2026-10-12	3	\N
1172	1102	missing	annual_physical	65	2026-10-12	3	\N
1173	1103	missing	annual_physical	65	2026-10-12	3	\N
1174	1104	missing	annual_physical	65	2026-10-12	3	\N
1175	1105	missing	annual_physical	65	2026-10-12	3	\N
1176	1106	missing	annual_physical	65	2026-10-12	3	\N
1177	1107	missing	annual_physical	65	2026-10-12	3	\N
1178	1108	missing	annual_physical	65	2026-10-12	3	\N
1179	1109	missing	annual_physical	65	2026-10-12	3	\N
1180	1110	missing	annual_physical	65	2026-10-12	3	\N
1181	1111	missing	annual_physical	65	2026-10-12	3	\N
1182	1112	missing	annual_physical	65	2026-10-12	3	\N
1183	1113	missing	annual_physical	65	2026-10-12	3	\N
1184	1114	missing	annual_physical	65	2026-10-12	3	\N
1185	1115	missing	annual_physical	65	2026-10-12	3	\N
1186	1116	missing	annual_physical	65	2026-10-12	3	\N
1187	1117	missing	annual_physical	65	2026-10-12	3	\N
1188	1118	missing	annual_physical	65	2026-10-12	3	\N
1189	1119	missing	annual_physical	65	2026-10-12	3	\N
1190	1120	missing	annual_physical	65	2026-10-12	3	\N
1191	1121	missing	annual_physical	65	2026-10-12	3	\N
1192	1122	missing	annual_physical	65	2026-10-12	3	\N
1193	1123	missing	annual_physical	65	2026-10-12	3	\N
1194	1124	missing	annual_physical	65	2026-10-12	3	\N
1195	1125	missing	annual_physical	65	2026-10-12	3	\N
1196	1126	missing	annual_physical	65	2026-10-12	3	\N
1197	1127	missing	annual_physical	65	2026-10-12	3	\N
1198	1128	missing	annual_physical	65	2026-10-12	3	\N
1199	1129	missing	annual_physical	65	2026-10-12	3	\N
1200	1130	missing	annual_physical	65	2026-10-12	3	\N
1201	1131	missing	annual_physical	65	2026-10-12	3	\N
1202	1132	missing	annual_physical	65	2026-10-12	3	\N
1203	1133	missing	annual_physical	65	2026-10-12	3	\N
1204	1134	missing	annual_physical	65	2026-10-12	3	\N
1205	1135	missing	annual_physical	65	2026-10-12	3	\N
1206	1136	missing	annual_physical	65	2026-10-12	3	\N
1207	1137	missing	annual_physical	65	2026-10-12	3	\N
1208	1138	missing	annual_physical	65	2026-10-12	3	\N
1209	1139	missing	annual_physical	65	2026-10-12	3	\N
1210	1140	missing	annual_physical	65	2026-10-12	3	\N
1211	1141	missing	annual_physical	65	2026-10-12	3	\N
1212	1142	missing	annual_physical	65	2026-10-12	3	\N
1213	1143	missing	annual_physical	65	2026-10-12	3	\N
1214	1144	missing	annual_physical	65	2026-10-12	3	\N
1215	1145	missing	annual_physical	65	2026-10-12	3	\N
1216	1146	missing	annual_physical	65	2026-10-12	3	\N
1217	1147	missing	annual_physical	65	2026-10-12	3	\N
1218	1148	missing	annual_physical	65	2026-10-12	3	\N
1219	1149	missing	annual_physical	65	2026-10-12	3	\N
1220	1150	missing	annual_physical	65	2026-10-12	3	\N
1221	1151	missing	annual_physical	65	2026-10-12	3	\N
1222	1152	missing	annual_physical	65	2026-10-12	3	\N
1223	1153	missing	annual_physical	65	2026-10-12	3	\N
1224	1154	missing	annual_physical	65	2026-10-12	3	\N
1225	1155	missing	annual_physical	65	2026-10-12	3	\N
1226	1156	missing	annual_physical	65	2026-10-12	3	\N
1227	1157	missing	annual_physical	65	2026-10-12	3	\N
1228	1158	missing	annual_physical	65	2026-10-12	3	\N
1229	1159	missing	annual_physical	65	2026-10-12	3	\N
1230	1160	missing	annual_physical	65	2026-10-12	3	\N
1231	1161	missing	annual_physical	65	2026-10-12	3	\N
1232	1162	missing	annual_physical	65	2026-10-12	3	\N
1233	1163	missing	annual_physical	65	2026-10-12	3	\N
1234	1164	missing	annual_physical	65	2026-10-12	3	\N
1235	1165	missing	annual_physical	65	2026-10-12	3	\N
1236	1166	missing	annual_physical	65	2026-10-12	3	\N
1237	1167	missing	annual_physical	65	2026-10-12	3	\N
1238	1168	missing	annual_physical	65	2026-10-12	3	\N
1239	1169	missing	annual_physical	65	2026-10-12	3	\N
1240	1170	missing	annual_physical	65	2026-10-12	3	\N
1241	1171	missing	annual_physical	65	2026-10-12	3	\N
1242	1172	missing	annual_physical	65	2026-10-12	3	\N
1243	1173	missing	annual_physical	65	2026-10-12	3	\N
1244	1174	missing	annual_physical	65	2026-10-12	3	\N
1245	1175	missing	annual_physical	65	2026-10-12	3	\N
1246	1176	missing	annual_physical	65	2026-10-12	3	\N
1247	1177	missing	annual_physical	65	2026-10-12	3	\N
1248	1178	missing	annual_physical	65	2026-10-12	3	\N
1249	1179	missing	annual_physical	65	2026-10-12	3	\N
1250	1180	missing	annual_physical	65	2026-10-12	3	\N
1251	1181	missing	annual_physical	65	2026-10-12	3	\N
1252	1182	missing	annual_physical	65	2026-10-12	3	\N
1253	1183	missing	annual_physical	65	2026-10-12	3	\N
1254	1184	missing	annual_physical	65	2026-10-12	3	\N
1255	1185	missing	annual_physical	65	2026-10-12	3	\N
1256	1186	missing	annual_physical	65	2026-10-12	3	\N
1257	1187	missing	annual_physical	65	2026-10-12	3	\N
1258	1188	missing	annual_physical	65	2026-10-12	3	\N
1259	1189	missing	annual_physical	65	2026-10-12	3	\N
1260	1190	missing	annual_physical	65	2026-10-12	3	\N
1261	1191	missing	annual_physical	65	2026-10-12	3	\N
1262	1192	missing	annual_physical	65	2026-10-12	3	\N
1263	1193	missing	annual_physical	65	2026-10-12	3	\N
1264	1194	missing	annual_physical	65	2026-10-12	3	\N
1265	1195	missing	annual_physical	65	2026-10-12	3	\N
1266	1196	missing	annual_physical	65	2026-10-12	3	\N
1267	1197	missing	annual_physical	65	2026-10-12	3	\N
1268	1198	missing	annual_physical	65	2026-10-12	3	\N
1269	1199	missing	annual_physical	65	2026-10-12	3	\N
1270	1200	missing	annual_physical	65	2026-10-12	3	\N
1271	1201	missing	annual_physical	65	2026-10-12	3	\N
1272	1202	missing	annual_physical	65	2026-10-12	3	\N
1273	1203	missing	annual_physical	65	2026-10-12	3	\N
1274	1204	missing	annual_physical	65	2026-10-12	3	\N
1275	1205	missing	annual_physical	65	2026-10-12	3	\N
1276	1206	missing	annual_physical	65	2026-10-12	3	\N
1277	1207	missing	annual_physical	65	2026-10-12	3	\N
1278	1208	missing	annual_physical	65	2026-10-12	3	\N
1279	1209	missing	annual_physical	65	2026-10-12	3	\N
1280	1210	missing	annual_physical	65	2026-10-12	3	\N
1281	1211	missing	annual_physical	65	2026-10-12	3	\N
1282	1212	missing	annual_physical	65	2026-10-12	3	\N
1283	1213	missing	annual_physical	65	2026-10-12	3	\N
1284	1214	missing	annual_physical	65	2026-10-12	3	\N
1285	1215	missing	annual_physical	65	2026-10-12	3	\N
1286	1216	missing	annual_physical	65	2026-10-12	3	\N
1287	1217	missing	annual_physical	65	2026-10-12	3	\N
1288	1218	missing	annual_physical	65	2026-10-12	3	\N
1289	1219	missing	annual_physical	65	2026-10-12	3	\N
1290	1220	missing	annual_physical	65	2026-10-12	3	\N
1291	1221	missing	annual_physical	65	2026-10-12	3	\N
1292	1222	missing	annual_physical	65	2026-10-12	3	\N
1293	1223	missing	annual_physical	65	2026-10-12	3	\N
1294	1224	missing	annual_physical	65	2026-10-12	3	\N
1295	1225	missing	annual_physical	65	2026-10-12	3	\N
1296	1226	missing	annual_physical	65	2026-10-12	3	\N
1297	1227	missing	annual_physical	65	2026-10-12	3	\N
1298	1228	missing	annual_physical	65	2026-10-12	3	\N
1299	1229	missing	annual_physical	65	2026-10-12	3	\N
1300	1230	missing	annual_physical	65	2026-10-12	3	\N
1301	1231	missing	annual_physical	65	2026-10-12	3	\N
1302	1232	missing	annual_physical	65	2026-10-12	3	\N
1303	1233	missing	annual_physical	65	2026-10-12	3	\N
1304	1234	missing	annual_physical	65	2026-10-12	3	\N
1305	1235	missing	annual_physical	65	2026-10-12	3	\N
1306	1236	missing	annual_physical	65	2026-10-12	3	\N
1307	1237	missing	annual_physical	65	2026-10-12	3	\N
1308	1238	missing	annual_physical	65	2026-10-12	3	\N
1309	1239	missing	annual_physical	65	2026-10-12	3	\N
1310	1240	missing	annual_physical	65	2026-10-12	3	\N
1311	1241	missing	annual_physical	65	2026-10-12	3	\N
1312	1242	missing	annual_physical	65	2026-10-12	3	\N
1313	1243	missing	annual_physical	65	2026-10-12	3	\N
1314	1244	missing	annual_physical	65	2026-10-12	3	\N
1315	1245	missing	annual_physical	65	2026-10-12	3	\N
1316	1246	missing	annual_physical	65	2026-10-12	3	\N
1317	1247	missing	annual_physical	65	2026-10-12	3	\N
1318	1248	missing	annual_physical	65	2026-10-12	3	\N
1319	1249	missing	annual_physical	65	2026-10-12	3	\N
1320	1250	missing	annual_physical	65	2026-10-12	3	\N
1321	1251	missing	annual_physical	65	2026-10-12	3	\N
1322	1252	missing	annual_physical	65	2026-10-12	3	\N
1323	1253	missing	annual_physical	65	2026-10-12	3	\N
1324	1254	missing	annual_physical	65	2026-10-12	3	\N
1325	1255	missing	annual_physical	65	2026-10-12	3	\N
1326	1256	missing	annual_physical	65	2026-10-12	3	\N
1327	1257	missing	annual_physical	65	2026-10-12	3	\N
1328	1258	missing	annual_physical	65	2026-10-12	3	\N
1329	1259	missing	annual_physical	65	2026-10-12	3	\N
1330	1260	missing	annual_physical	65	2026-10-12	3	\N
1331	1261	missing	annual_physical	65	2026-10-12	3	\N
1332	1262	missing	annual_physical	65	2026-10-12	3	\N
1333	1263	missing	annual_physical	65	2026-10-12	3	\N
1334	1264	missing	annual_physical	65	2026-10-12	3	\N
1335	1265	missing	annual_physical	65	2026-10-12	3	\N
1336	1266	missing	annual_physical	65	2026-10-12	3	\N
1337	1267	missing	annual_physical	65	2026-10-12	3	\N
1338	1268	missing	annual_physical	65	2026-10-12	3	\N
1339	1269	missing	annual_physical	65	2026-10-12	3	\N
1340	1270	missing	annual_physical	65	2026-10-12	3	\N
1341	1271	missing	annual_physical	65	2026-10-12	3	\N
1342	1272	missing	annual_physical	65	2026-10-12	3	\N
1343	1273	missing	annual_physical	65	2026-10-12	3	\N
1344	1274	missing	annual_physical	65	2026-10-12	3	\N
1345	1275	missing	annual_physical	65	2026-10-12	3	\N
1346	1276	missing	annual_physical	65	2026-10-12	3	\N
1347	1277	missing	annual_physical	65	2026-10-12	3	\N
1348	1278	missing	annual_physical	65	2026-10-12	3	\N
1349	1279	missing	annual_physical	65	2026-10-12	3	\N
1350	1280	missing	annual_physical	65	2026-10-12	3	\N
1351	1281	missing	annual_physical	65	2026-10-12	3	\N
1352	1282	missing	annual_physical	65	2026-10-12	3	\N
1353	1283	missing	annual_physical	65	2026-10-12	3	\N
1354	1284	missing	annual_physical	65	2026-10-12	3	\N
1355	1285	missing	annual_physical	65	2026-10-12	3	\N
1356	1286	missing	annual_physical	65	2026-10-12	3	\N
1357	1287	missing	annual_physical	65	2026-10-12	3	\N
1358	1288	missing	annual_physical	65	2026-10-12	3	\N
1359	1289	missing	annual_physical	65	2026-10-12	3	\N
1360	1290	missing	annual_physical	65	2026-10-12	3	\N
1361	1291	missing	annual_physical	65	2026-10-12	3	\N
1362	1292	missing	annual_physical	65	2026-10-12	3	\N
1363	1293	missing	annual_physical	65	2026-10-12	3	\N
1364	1294	missing	annual_physical	65	2026-10-12	3	\N
1365	1295	missing	annual_physical	65	2026-10-12	3	\N
1366	1296	missing	annual_physical	65	2026-10-12	3	\N
1367	1297	missing	annual_physical	65	2026-10-12	3	\N
1368	1298	missing	annual_physical	65	2026-10-12	3	\N
1369	1299	missing	annual_physical	65	2026-10-12	3	\N
1370	1300	missing	annual_physical	65	2026-10-12	3	\N
1371	1301	missing	annual_physical	65	2026-10-12	3	\N
1372	1302	missing	annual_physical	65	2026-10-12	3	\N
1373	1303	missing	annual_physical	65	2026-10-12	3	\N
1374	1304	missing	annual_physical	65	2026-10-12	3	\N
1375	1305	missing	annual_physical	65	2026-10-12	3	\N
1376	1306	missing	annual_physical	65	2026-10-12	3	\N
1377	1307	missing	annual_physical	65	2026-10-12	3	\N
1378	1308	missing	annual_physical	65	2026-10-12	3	\N
1379	1309	missing	annual_physical	65	2026-10-12	3	\N
1380	1310	missing	annual_physical	65	2026-10-12	3	\N
1381	1311	missing	annual_physical	65	2026-10-12	3	\N
1382	1312	missing	annual_physical	65	2026-10-12	3	\N
1383	1313	missing	annual_physical	65	2026-10-12	3	\N
1384	1314	missing	annual_physical	65	2026-10-12	3	\N
1385	1315	missing	annual_physical	65	2026-10-12	3	\N
1386	1316	missing	annual_physical	65	2026-10-12	3	\N
1387	1317	missing	annual_physical	65	2026-10-12	3	\N
1388	1318	missing	annual_physical	65	2026-10-12	3	\N
1389	1319	missing	annual_physical	65	2026-10-12	3	\N
1390	1320	missing	annual_physical	65	2026-10-12	3	\N
1391	1321	missing	annual_physical	65	2026-10-12	3	\N
1392	1322	borrowed	annual_physical	65	2026-10-12	3	\N
1393	1323	missing	annual_physical	65	2026-10-12	3	\N
1394	1324	missing	annual_physical	65	2026-10-12	3	\N
1395	1325	missing	annual_physical	65	2026-10-12	3	\N
1396	1326	missing	annual_physical	65	2026-10-12	3	\N
1397	1327	missing	annual_physical	65	2026-10-12	3	\N
1398	1328	missing	annual_physical	65	2026-10-12	3	\N
1399	1329	missing	annual_physical	65	2026-10-12	3	\N
1400	1330	missing	annual_physical	65	2026-10-12	3	\N
1401	1331	missing	annual_physical	65	2026-10-12	3	\N
1402	1332	missing	annual_physical	65	2026-10-12	3	\N
1403	1333	missing	annual_physical	65	2026-10-12	3	\N
1404	1334	missing	annual_physical	65	2026-10-12	3	\N
1405	1335	missing	annual_physical	65	2026-10-12	3	\N
1406	1336	missing	annual_physical	65	2026-10-12	3	\N
1407	1337	missing	annual_physical	65	2026-10-12	3	\N
1408	1338	missing	annual_physical	65	2026-10-12	3	\N
1409	1339	missing	annual_physical	65	2026-10-12	3	\N
1410	1340	missing	annual_physical	65	2026-10-12	3	\N
1411	1341	missing	annual_physical	65	2026-10-12	3	\N
1412	1342	missing	annual_physical	65	2026-10-12	3	\N
1413	1343	missing	annual_physical	65	2026-10-12	3	\N
1414	1344	missing	annual_physical	65	2026-10-12	3	\N
1415	1345	missing	annual_physical	65	2026-10-12	3	\N
1416	1346	missing	annual_physical	65	2026-10-12	3	\N
104	1347	available	annual_physical	65	2026-10-12	3	\N
1417	1348	missing	annual_physical	65	2026-10-12	3	\N
1418	1349	missing	annual_physical	65	2026-10-12	3	\N
1419	1350	missing	annual_physical	65	2026-10-12	3	\N
1420	1351	missing	annual_physical	65	2026-10-12	3	\N
1421	1352	missing	annual_physical	65	2026-10-12	3	\N
1422	1353	missing	annual_physical	65	2026-10-12	3	\N
1423	1354	missing	annual_physical	65	2026-10-12	3	\N
1424	1355	missing	annual_physical	65	2026-10-12	3	\N
1425	1356	missing	annual_physical	65	2026-10-12	3	\N
1426	1357	missing	annual_physical	65	2026-10-12	3	\N
1427	1358	missing	annual_physical	65	2026-10-12	3	\N
1428	1359	missing	annual_physical	65	2026-10-12	3	\N
1429	1360	missing	annual_physical	65	2026-10-12	3	\N
1430	1361	missing	annual_physical	65	2026-10-12	3	\N
1431	1362	missing	annual_physical	65	2026-10-12	3	\N
1432	1363	missing	annual_physical	65	2026-10-12	3	\N
1433	1364	missing	annual_physical	65	2026-10-12	3	\N
1434	1365	missing	annual_physical	65	2026-10-12	3	\N
1435	1366	missing	annual_physical	65	2026-10-12	3	\N
1436	1367	missing	annual_physical	65	2026-10-12	3	\N
1437	1368	missing	annual_physical	65	2026-10-12	3	\N
1438	1369	missing	annual_physical	65	2026-10-12	3	\N
1439	1370	missing	annual_physical	65	2026-10-12	3	\N
1440	1371	missing	annual_physical	65	2026-10-12	3	\N
1441	1372	missing	annual_physical	65	2026-10-12	3	\N
1442	1373	missing	annual_physical	65	2026-10-12	3	\N
1443	1374	missing	annual_physical	65	2026-10-12	3	\N
1444	1375	missing	annual_physical	65	2026-10-12	3	\N
1445	1376	missing	annual_physical	65	2026-10-12	3	\N
1446	1377	missing	annual_physical	65	2026-10-12	3	\N
1447	1378	missing	annual_physical	65	2026-10-12	3	\N
1448	1379	missing	annual_physical	65	2026-10-12	3	\N
1449	1380	missing	annual_physical	65	2026-10-12	3	\N
1450	1381	missing	annual_physical	65	2026-10-12	3	\N
1451	1382	missing	annual_physical	65	2026-10-12	3	\N
1452	1383	missing	annual_physical	65	2026-10-12	3	\N
1453	1384	missing	annual_physical	65	2026-10-12	3	\N
1454	1385	missing	annual_physical	65	2026-10-12	3	\N
1455	1386	missing	annual_physical	65	2026-10-12	3	\N
1456	1387	missing	annual_physical	65	2026-10-12	3	\N
1457	1388	missing	annual_physical	65	2026-10-12	3	\N
1458	1389	missing	annual_physical	65	2026-10-12	3	\N
1459	1390	missing	annual_physical	65	2026-10-12	3	\N
1460	1391	missing	annual_physical	65	2026-10-12	3	\N
1461	1392	missing	annual_physical	65	2026-10-12	3	\N
1462	1393	missing	annual_physical	65	2026-10-12	3	\N
1463	1394	missing	annual_physical	65	2026-10-12	3	\N
1464	1395	missing	annual_physical	65	2026-10-12	3	\N
1465	1396	missing	annual_physical	65	2026-10-12	3	\N
1466	1397	missing	annual_physical	65	2026-10-12	3	\N
1467	1398	missing	annual_physical	65	2026-10-12	3	\N
1468	1399	missing	annual_physical	65	2026-10-12	3	\N
1469	1400	missing	annual_physical	65	2026-10-12	3	\N
1470	1401	missing	annual_physical	65	2026-10-12	3	\N
1471	1402	missing	annual_physical	65	2026-10-12	3	\N
1472	1403	missing	annual_physical	65	2026-10-12	3	\N
1473	1404	missing	annual_physical	65	2026-10-12	3	\N
1474	1405	missing	annual_physical	65	2026-10-12	3	\N
1475	1406	missing	annual_physical	65	2026-10-12	3	\N
1476	1407	missing	annual_physical	65	2026-10-12	3	\N
1477	1408	missing	annual_physical	65	2026-10-12	3	\N
1478	1409	missing	annual_physical	65	2026-10-12	3	\N
1479	1410	missing	annual_physical	65	2026-10-12	3	\N
1480	1411	missing	annual_physical	65	2026-10-12	3	\N
1481	1412	missing	annual_physical	65	2026-10-12	3	\N
1482	1413	missing	annual_physical	65	2026-10-12	3	\N
1483	1414	missing	annual_physical	65	2026-10-12	3	\N
1484	1415	missing	annual_physical	65	2026-10-12	3	\N
1485	1416	missing	annual_physical	65	2026-10-12	3	\N
1486	1417	missing	annual_physical	65	2026-10-12	3	\N
1487	1418	missing	annual_physical	65	2026-10-12	3	\N
1488	1419	missing	annual_physical	65	2026-10-12	3	\N
1489	1420	missing	annual_physical	65	2026-10-12	3	\N
1490	1421	missing	annual_physical	65	2026-10-12	3	\N
1491	1422	missing	annual_physical	65	2026-10-12	3	\N
1492	1423	missing	annual_physical	65	2026-10-12	3	\N
1493	1424	missing	annual_physical	65	2026-10-12	3	\N
1494	1425	missing	annual_physical	65	2026-10-12	3	\N
1495	1426	missing	annual_physical	65	2026-10-12	3	\N
1496	1427	missing	annual_physical	65	2026-10-12	3	\N
1497	1428	missing	annual_physical	65	2026-10-12	3	\N
1498	1429	missing	annual_physical	65	2026-10-12	3	\N
1499	1430	missing	annual_physical	65	2026-10-12	3	\N
1500	1431	missing	annual_physical	65	2026-10-12	3	\N
1501	1432	missing	annual_physical	65	2026-10-12	3	\N
1502	1433	missing	annual_physical	65	2026-10-12	3	\N
1503	1434	missing	annual_physical	65	2026-10-12	3	\N
1504	1435	missing	annual_physical	65	2026-10-12	3	\N
1505	1436	missing	annual_physical	65	2026-10-12	3	\N
1506	1437	missing	annual_physical	65	2026-10-12	3	\N
1507	1438	missing	annual_physical	65	2026-10-12	3	\N
1508	1439	missing	annual_physical	65	2026-10-12	3	\N
1509	1440	missing	annual_physical	65	2026-10-12	3	\N
1510	1441	missing	annual_physical	65	2026-10-12	3	\N
1511	1442	missing	annual_physical	65	2026-10-12	3	\N
1512	1443	missing	annual_physical	65	2026-10-12	3	\N
1513	1444	missing	annual_physical	65	2026-10-12	3	\N
1514	1445	missing	annual_physical	65	2026-10-12	3	\N
1515	1446	missing	annual_physical	65	2026-10-12	3	\N
1516	1447	missing	annual_physical	65	2026-10-12	3	\N
1517	1448	missing	annual_physical	65	2026-10-12	3	\N
1518	1449	missing	annual_physical	65	2026-10-12	3	\N
1519	1450	missing	annual_physical	65	2026-10-12	3	\N
1520	1451	missing	annual_physical	65	2026-10-12	3	\N
1521	1452	missing	annual_physical	65	2026-10-12	3	\N
1522	1453	missing	annual_physical	65	2026-10-12	3	\N
1523	1454	missing	annual_physical	65	2026-10-12	3	\N
1524	1455	missing	annual_physical	65	2026-10-12	3	\N
1525	1456	missing	annual_physical	65	2026-10-12	3	\N
1526	1457	missing	annual_physical	65	2026-10-12	3	\N
1527	1458	missing	annual_physical	65	2026-10-12	3	\N
1528	1459	missing	annual_physical	65	2026-10-12	3	\N
1529	1460	missing	annual_physical	65	2026-10-12	3	\N
1530	1461	missing	annual_physical	65	2026-10-12	3	\N
1531	1462	missing	annual_physical	65	2026-10-12	3	\N
1532	1463	missing	annual_physical	65	2026-10-12	3	\N
1533	1464	missing	annual_physical	65	2026-10-12	3	\N
1534	1465	missing	annual_physical	65	2026-10-12	3	\N
1535	1466	missing	annual_physical	65	2026-10-12	3	\N
1536	1467	missing	annual_physical	65	2026-10-12	3	\N
1537	1468	missing	annual_physical	65	2026-10-12	3	\N
1538	1469	missing	annual_physical	65	2026-10-12	3	\N
1539	1470	missing	annual_physical	65	2026-10-12	3	\N
1540	1471	missing	annual_physical	65	2026-10-12	3	\N
1541	1472	missing	annual_physical	65	2026-10-12	3	\N
1542	1473	missing	annual_physical	65	2026-10-12	3	\N
1543	1474	missing	annual_physical	65	2026-10-12	3	\N
1544	1475	missing	annual_physical	65	2026-10-12	3	\N
1545	1476	missing	annual_physical	65	2026-10-12	3	\N
1546	1477	missing	annual_physical	65	2026-10-12	3	\N
1547	1478	missing	annual_physical	65	2026-10-12	3	\N
1548	1479	missing	annual_physical	65	2026-10-12	3	\N
1549	1480	missing	annual_physical	65	2026-10-12	3	\N
1550	1481	missing	annual_physical	65	2026-10-12	3	\N
1551	1482	missing	annual_physical	65	2026-10-12	3	\N
1552	1483	missing	annual_physical	65	2026-10-12	3	\N
1553	1484	missing	annual_physical	65	2026-10-12	3	\N
1554	1485	missing	annual_physical	65	2026-10-12	3	\N
1555	1486	missing	annual_physical	65	2026-10-12	3	\N
1556	1487	missing	annual_physical	65	2026-10-12	3	\N
1557	1488	missing	annual_physical	65	2026-10-12	3	\N
1558	1489	missing	annual_physical	65	2026-10-12	3	\N
1559	1490	missing	annual_physical	65	2026-10-12	3	\N
1560	1491	missing	annual_physical	65	2026-10-12	3	\N
1561	1492	missing	annual_physical	65	2026-10-12	3	\N
1562	1493	missing	annual_physical	65	2026-10-12	3	\N
1563	1494	missing	annual_physical	65	2026-10-12	3	\N
1564	1495	missing	annual_physical	65	2026-10-12	3	\N
1565	1496	missing	annual_physical	65	2026-10-12	3	\N
1566	1497	missing	annual_physical	65	2026-10-12	3	\N
1567	1498	missing	annual_physical	65	2026-10-12	3	\N
1568	1499	missing	annual_physical	65	2026-10-12	3	\N
1569	1500	missing	annual_physical	65	2026-10-12	3	\N
1570	1501	missing	annual_physical	65	2026-10-12	3	\N
1571	1502	missing	annual_physical	65	2026-10-12	3	\N
1572	1503	missing	annual_physical	65	2026-10-12	3	\N
1573	1504	missing	annual_physical	65	2026-10-12	3	\N
1574	1505	missing	annual_physical	65	2026-10-12	3	\N
1575	1506	missing	annual_physical	65	2026-10-12	3	\N
1576	1507	missing	annual_physical	65	2026-10-12	3	\N
1577	1508	missing	annual_physical	65	2026-10-12	3	\N
1578	1509	missing	annual_physical	65	2026-10-12	3	\N
1579	1510	missing	annual_physical	65	2026-10-12	3	\N
1580	1511	missing	annual_physical	65	2026-10-12	3	\N
1581	1512	missing	annual_physical	65	2026-10-12	3	\N
1582	1513	missing	annual_physical	65	2026-10-12	3	\N
1583	1514	missing	annual_physical	65	2026-10-12	3	\N
1584	1515	missing	annual_physical	65	2026-10-12	3	\N
1585	1516	missing	annual_physical	65	2026-10-12	3	\N
1586	1517	missing	annual_physical	65	2026-10-12	3	\N
1587	1518	missing	annual_physical	65	2026-10-12	3	\N
1588	1519	missing	annual_physical	65	2026-10-12	3	\N
1589	1520	missing	annual_physical	65	2026-10-12	3	\N
1590	1521	missing	annual_physical	65	2026-10-12	3	\N
1591	1522	missing	annual_physical	65	2026-10-12	3	\N
1592	1523	missing	annual_physical	65	2026-10-12	3	\N
1593	1524	missing	annual_physical	65	2026-10-12	3	\N
1594	1525	missing	annual_physical	65	2026-10-12	3	\N
1595	1526	missing	annual_physical	65	2026-10-12	3	\N
1596	1527	missing	annual_physical	65	2026-10-12	3	\N
1597	1528	missing	annual_physical	65	2026-10-12	3	\N
1598	1529	missing	annual_physical	65	2026-10-12	3	\N
1599	1530	missing	annual_physical	65	2026-10-12	3	\N
1600	1531	missing	annual_physical	65	2026-10-12	3	\N
1601	1532	missing	annual_physical	65	2026-10-12	3	\N
1602	1533	missing	annual_physical	65	2026-10-12	3	\N
1603	1534	missing	annual_physical	65	2026-10-12	3	\N
1604	1535	missing	annual_physical	65	2026-10-12	3	\N
1605	1536	missing	annual_physical	65	2026-10-12	3	\N
1606	1537	missing	annual_physical	65	2026-10-12	3	\N
1607	1538	missing	annual_physical	65	2026-10-12	3	\N
1608	1539	missing	annual_physical	65	2026-10-12	3	\N
1609	1540	missing	annual_physical	65	2026-10-12	3	\N
1610	1541	missing	annual_physical	65	2026-10-12	3	\N
1611	1542	missing	annual_physical	65	2026-10-12	3	\N
1612	1543	missing	annual_physical	65	2026-10-12	3	\N
1613	1544	missing	annual_physical	65	2026-10-12	3	\N
1614	1545	missing	annual_physical	65	2026-10-12	3	\N
1615	1546	missing	annual_physical	65	2026-10-12	3	\N
1616	1547	missing	annual_physical	65	2026-10-12	3	\N
1617	1548	missing	annual_physical	65	2026-10-12	3	\N
1618	1549	missing	annual_physical	65	2026-10-12	3	\N
1619	1550	missing	annual_physical	65	2026-10-12	3	\N
1620	1551	missing	annual_physical	65	2026-10-12	3	\N
1621	1552	missing	annual_physical	65	2026-10-12	3	\N
1622	1553	missing	annual_physical	65	2026-10-12	3	\N
1623	1554	missing	annual_physical	65	2026-10-12	3	\N
1624	1555	missing	annual_physical	65	2026-10-12	3	\N
1625	1556	missing	annual_physical	65	2026-10-12	3	\N
1626	1557	missing	annual_physical	65	2026-10-12	3	\N
1627	1558	missing	annual_physical	65	2026-10-12	3	\N
1628	1559	missing	annual_physical	65	2026-10-12	3	\N
1629	1560	missing	annual_physical	65	2026-10-12	3	\N
1630	1561	missing	annual_physical	65	2026-10-12	3	\N
1631	1562	missing	annual_physical	65	2026-10-12	3	\N
1632	1563	missing	annual_physical	65	2026-10-12	3	\N
1633	1564	missing	annual_physical	65	2026-10-12	3	\N
1634	1565	missing	annual_physical	65	2026-10-12	3	\N
1635	1566	missing	annual_physical	65	2026-10-12	3	\N
1636	1567	missing	annual_physical	65	2026-10-12	3	\N
1637	1568	missing	annual_physical	65	2026-10-12	3	\N
1638	1569	missing	annual_physical	65	2026-10-12	3	\N
1639	1570	missing	annual_physical	65	2026-10-12	3	\N
1640	1571	missing	annual_physical	65	2026-10-12	3	\N
1641	1572	missing	annual_physical	65	2026-10-12	3	\N
1642	1573	missing	annual_physical	65	2026-10-12	3	\N
1643	1574	missing	annual_physical	65	2026-10-12	3	\N
1644	1575	missing	annual_physical	65	2026-10-12	3	\N
1645	1576	missing	annual_physical	65	2026-10-12	3	\N
1646	1577	missing	annual_physical	65	2026-10-12	3	\N
1647	1578	missing	annual_physical	65	2026-10-12	3	\N
1648	1579	missing	annual_physical	65	2026-10-12	3	\N
1649	1580	missing	annual_physical	65	2026-10-12	3	\N
1650	1581	missing	annual_physical	65	2026-10-12	3	\N
1651	1582	missing	annual_physical	65	2026-10-12	3	\N
1652	1583	missing	annual_physical	65	2026-10-12	3	\N
1653	1584	missing	annual_physical	65	2026-10-12	3	\N
1654	1585	missing	annual_physical	65	2026-10-12	3	\N
1655	1586	missing	annual_physical	65	2026-10-12	3	\N
1656	1587	missing	annual_physical	65	2026-10-12	3	\N
1657	1588	missing	annual_physical	65	2026-10-12	3	\N
1658	1589	missing	annual_physical	65	2026-10-12	3	\N
1659	1590	missing	annual_physical	65	2026-10-12	3	\N
1660	1591	missing	annual_physical	65	2026-10-12	3	\N
1661	1592	missing	annual_physical	65	2026-10-12	3	\N
1662	1593	missing	annual_physical	65	2026-10-12	3	\N
1663	1594	missing	annual_physical	65	2026-10-12	3	\N
1664	1595	missing	annual_physical	65	2026-10-12	3	\N
1665	1596	missing	annual_physical	65	2026-10-12	3	\N
1666	1597	missing	annual_physical	65	2026-10-12	3	\N
1667	1598	missing	annual_physical	65	2026-10-12	3	\N
1668	1599	missing	annual_physical	65	2026-10-12	3	\N
1669	1600	missing	annual_physical	65	2026-10-12	3	\N
1670	1601	missing	annual_physical	65	2026-10-12	3	\N
1671	1602	missing	annual_physical	65	2026-10-12	3	\N
1672	1603	missing	annual_physical	65	2026-10-12	3	\N
1673	1604	missing	annual_physical	65	2026-10-12	3	\N
1674	1605	missing	annual_physical	65	2026-10-12	3	\N
1675	1606	missing	annual_physical	65	2026-10-12	3	\N
1676	1607	missing	annual_physical	65	2026-10-12	3	\N
1677	1608	missing	annual_physical	65	2026-10-12	3	\N
1678	1609	missing	annual_physical	65	2026-10-12	3	\N
1679	1610	missing	annual_physical	65	2026-10-12	3	\N
1680	1611	missing	annual_physical	65	2026-10-12	3	\N
1681	1612	missing	annual_physical	65	2026-10-12	3	\N
1682	1613	missing	annual_physical	65	2026-10-12	3	\N
1683	1614	missing	annual_physical	65	2026-10-12	3	\N
1684	1615	missing	annual_physical	65	2026-10-12	3	\N
1685	1616	missing	annual_physical	65	2026-10-12	3	\N
1686	1617	missing	annual_physical	65	2026-10-12	3	\N
1687	1618	missing	annual_physical	65	2026-10-12	3	\N
1688	1619	missing	annual_physical	65	2026-10-12	3	\N
1689	1620	missing	annual_physical	65	2026-10-12	3	\N
1690	1621	borrowed	annual_physical	65	2026-10-12	3	\N
1691	1622	missing	annual_physical	65	2026-10-12	3	\N
1692	1623	missing	annual_physical	65	2026-10-12	3	\N
1693	1624	missing	annual_physical	65	2026-10-12	3	\N
1694	1625	missing	annual_physical	65	2026-10-12	3	\N
1695	1626	missing	annual_physical	65	2026-10-12	3	\N
1696	1627	missing	annual_physical	65	2026-10-12	3	\N
1697	1628	missing	annual_physical	65	2026-10-12	3	\N
1698	1629	missing	annual_physical	65	2026-10-12	3	\N
1699	1630	missing	annual_physical	65	2026-10-12	3	\N
1700	1631	missing	annual_physical	65	2026-10-12	3	\N
1701	1632	missing	annual_physical	65	2026-10-12	3	\N
1702	1633	missing	annual_physical	65	2026-10-12	3	\N
1703	1634	missing	annual_physical	65	2026-10-12	3	\N
1704	1635	missing	annual_physical	65	2026-10-12	3	\N
1705	1636	missing	annual_physical	65	2026-10-12	3	\N
1706	1637	missing	annual_physical	65	2026-10-12	3	\N
1707	1638	missing	annual_physical	65	2026-10-12	3	\N
1708	1639	missing	annual_physical	65	2026-10-12	3	\N
1709	1640	missing	annual_physical	65	2026-10-12	3	\N
1710	1641	missing	annual_physical	65	2026-10-12	3	\N
1711	1642	missing	annual_physical	65	2026-10-12	3	\N
1712	1643	missing	annual_physical	65	2026-10-12	3	\N
1713	1644	missing	annual_physical	65	2026-10-12	3	\N
1714	1645	missing	annual_physical	65	2026-10-12	3	\N
1715	1646	missing	annual_physical	65	2026-10-12	3	\N
1716	1647	missing	annual_physical	65	2026-10-12	3	\N
1717	1648	missing	annual_physical	65	2026-10-12	3	\N
1718	1649	missing	annual_physical	65	2026-10-12	3	\N
1719	1650	missing	annual_physical	65	2026-10-12	3	\N
1720	1651	missing	annual_physical	65	2026-10-12	3	\N
1721	1652	missing	annual_physical	65	2026-10-12	3	\N
1722	1653	missing	annual_physical	65	2026-10-12	3	\N
1723	1654	missing	annual_physical	65	2026-10-12	3	\N
1724	1655	missing	annual_physical	65	2026-10-12	3	\N
1725	1656	missing	annual_physical	65	2026-10-12	3	\N
1726	1657	missing	annual_physical	65	2026-10-12	3	\N
1727	1658	missing	annual_physical	65	2026-10-12	3	\N
1728	1659	missing	annual_physical	65	2026-10-12	3	\N
1729	1660	missing	annual_physical	65	2026-10-12	3	\N
1730	1661	missing	annual_physical	65	2026-10-12	3	\N
1731	1662	missing	annual_physical	65	2026-10-12	3	\N
1732	1663	missing	annual_physical	65	2026-10-12	3	\N
1733	1664	missing	annual_physical	65	2026-10-12	3	\N
1734	1665	missing	annual_physical	65	2026-10-12	3	\N
1735	1666	missing	annual_physical	65	2026-10-12	3	\N
1736	1667	missing	annual_physical	65	2026-10-12	3	\N
1737	1668	missing	annual_physical	65	2026-10-12	3	\N
1738	1669	missing	annual_physical	65	2026-10-12	3	\N
1739	1670	missing	annual_physical	65	2026-10-12	3	\N
1740	1671	missing	annual_physical	65	2026-10-12	3	\N
1741	1672	missing	annual_physical	65	2026-10-12	3	\N
1742	1673	missing	annual_physical	65	2026-10-12	3	\N
1743	1674	missing	annual_physical	65	2026-10-12	3	\N
1744	1675	missing	annual_physical	65	2026-10-12	3	\N
1745	1676	missing	annual_physical	65	2026-10-12	3	\N
1746	1677	missing	annual_physical	65	2026-10-12	3	\N
1747	1678	missing	annual_physical	65	2026-10-12	3	\N
1748	1679	missing	annual_physical	65	2026-10-12	3	\N
1749	1680	missing	annual_physical	65	2026-10-12	3	\N
1750	1681	missing	annual_physical	65	2026-10-12	3	\N
1751	1682	missing	annual_physical	65	2026-10-12	3	\N
1752	1683	missing	annual_physical	65	2026-10-12	3	\N
1753	1684	missing	annual_physical	65	2026-10-12	3	\N
1754	1685	missing	annual_physical	65	2026-10-12	3	\N
1755	1686	missing	annual_physical	65	2026-10-12	3	\N
1756	1687	missing	annual_physical	65	2026-10-12	3	\N
1757	1688	missing	annual_physical	65	2026-10-12	3	\N
1758	1689	missing	annual_physical	65	2026-10-12	3	\N
1759	1690	missing	annual_physical	65	2026-10-12	3	\N
1760	1691	missing	annual_physical	65	2026-10-12	3	\N
1761	1692	missing	annual_physical	65	2026-10-12	3	\N
1762	1693	missing	annual_physical	65	2026-10-12	3	\N
1763	1694	missing	annual_physical	65	2026-10-12	3	\N
1764	1695	missing	annual_physical	65	2026-10-12	3	\N
1765	1696	missing	annual_physical	65	2026-10-12	3	\N
1766	1697	missing	annual_physical	65	2026-10-12	3	\N
1767	1698	missing	annual_physical	65	2026-10-12	3	\N
1768	1699	missing	annual_physical	65	2026-10-12	3	\N
1769	1700	missing	annual_physical	65	2026-10-12	3	\N
1770	1701	missing	annual_physical	65	2026-10-12	3	\N
1771	1702	missing	annual_physical	65	2026-10-12	3	\N
1772	1703	missing	annual_physical	65	2026-10-12	3	\N
1773	1704	missing	annual_physical	65	2026-10-12	3	\N
1774	1705	missing	annual_physical	65	2026-10-12	3	\N
1775	1706	missing	annual_physical	65	2026-10-12	3	\N
1776	1707	missing	annual_physical	65	2026-10-12	3	\N
1777	1708	missing	annual_physical	65	2026-10-12	3	\N
1778	1709	missing	annual_physical	65	2026-10-12	3	\N
1779	1710	borrowed	annual_physical	65	2026-10-12	3	\N
1780	1711	missing	annual_physical	65	2026-10-12	3	\N
1781	1712	missing	annual_physical	65	2026-10-12	3	\N
1782	1713	missing	annual_physical	65	2026-10-12	3	\N
1783	1714	missing	annual_physical	65	2026-10-12	3	\N
1784	1715	missing	annual_physical	65	2026-10-12	3	\N
1785	1716	missing	annual_physical	65	2026-10-12	3	\N
1786	1717	missing	annual_physical	65	2026-10-12	3	\N
1787	1718	missing	annual_physical	65	2026-10-12	3	\N
1788	1719	missing	annual_physical	65	2026-10-12	3	\N
1789	1720	missing	annual_physical	65	2026-10-12	3	\N
1790	1721	missing	annual_physical	65	2026-10-12	3	\N
1791	1722	missing	annual_physical	65	2026-10-12	3	\N
1792	1723	missing	annual_physical	65	2026-10-12	3	\N
1793	1724	missing	annual_physical	65	2026-10-12	3	\N
1794	1725	missing	annual_physical	65	2026-10-12	3	\N
1795	1726	missing	annual_physical	65	2026-10-12	3	\N
1796	1727	missing	annual_physical	65	2026-10-12	3	\N
1797	1728	missing	annual_physical	65	2026-10-12	3	\N
1798	1729	missing	annual_physical	65	2026-10-12	3	\N
1799	1730	missing	annual_physical	65	2026-10-12	3	\N
1800	1731	missing	annual_physical	65	2026-10-12	3	\N
1801	1732	missing	annual_physical	65	2026-10-12	3	\N
1802	1733	missing	annual_physical	65	2026-10-12	3	\N
1803	1734	missing	annual_physical	65	2026-10-12	3	\N
1804	1735	missing	annual_physical	65	2026-10-12	3	\N
1805	1736	missing	annual_physical	65	2026-10-12	3	\N
1806	1737	missing	annual_physical	65	2026-10-12	3	\N
1807	1738	missing	annual_physical	65	2026-10-12	3	\N
1808	1739	missing	annual_physical	65	2026-10-12	3	\N
1809	1740	missing	annual_physical	65	2026-10-12	3	\N
1810	1741	missing	annual_physical	65	2026-10-12	3	\N
1811	1742	missing	annual_physical	65	2026-10-12	3	\N
1812	1743	missing	annual_physical	65	2026-10-12	3	\N
1813	1744	missing	annual_physical	65	2026-10-12	3	\N
1814	1745	missing	annual_physical	65	2026-10-12	3	\N
1815	1746	missing	annual_physical	65	2026-10-12	3	\N
1816	1747	missing	annual_physical	65	2026-10-12	3	\N
1817	1748	missing	annual_physical	65	2026-10-12	3	\N
1818	1749	missing	annual_physical	65	2026-10-12	3	\N
1819	1750	missing	annual_physical	65	2026-10-12	3	\N
1820	1751	missing	annual_physical	65	2026-10-12	3	\N
1821	1752	missing	annual_physical	65	2026-10-12	3	\N
1822	1753	missing	annual_physical	65	2026-10-12	3	\N
1823	1754	missing	annual_physical	65	2026-10-12	3	\N
1824	1755	missing	annual_physical	65	2026-10-12	3	\N
1825	1756	missing	annual_physical	65	2026-10-12	3	\N
1826	1757	missing	annual_physical	65	2026-10-12	3	\N
1827	1758	missing	annual_physical	65	2026-10-12	3	\N
1828	1759	missing	annual_physical	65	2026-10-12	3	\N
1829	1760	missing	annual_physical	65	2026-10-12	3	\N
1830	1761	missing	annual_physical	65	2026-10-12	3	\N
1831	1762	missing	annual_physical	65	2026-10-12	3	\N
1832	1763	missing	annual_physical	65	2026-10-12	3	\N
1833	1764	missing	annual_physical	65	2026-10-12	3	\N
1834	1765	missing	annual_physical	65	2026-10-12	3	\N
1835	1766	missing	annual_physical	65	2026-10-12	3	\N
1836	1767	missing	annual_physical	65	2026-10-12	3	\N
1837	1768	missing	annual_physical	65	2026-10-12	3	\N
1838	1769	missing	annual_physical	65	2026-10-12	3	\N
1839	1770	missing	annual_physical	65	2026-10-12	3	\N
1840	1771	missing	annual_physical	65	2026-10-12	3	\N
1841	1772	missing	annual_physical	65	2026-10-12	3	\N
1842	1773	missing	annual_physical	65	2026-10-12	3	\N
1843	1774	missing	annual_physical	65	2026-10-12	3	\N
1844	1775	missing	annual_physical	65	2026-10-12	3	\N
1845	1776	missing	annual_physical	65	2026-10-12	3	\N
1846	1777	missing	annual_physical	65	2026-10-12	3	\N
1847	1778	missing	annual_physical	65	2026-10-12	3	\N
1848	1779	missing	annual_physical	65	2026-10-12	3	\N
1849	1780	missing	annual_physical	65	2026-10-12	3	\N
1850	1781	missing	annual_physical	65	2026-10-12	3	\N
1851	1782	missing	annual_physical	65	2026-10-12	3	\N
1852	1783	missing	annual_physical	65	2026-10-12	3	\N
1853	1784	missing	annual_physical	65	2026-10-12	3	\N
1854	1785	missing	annual_physical	65	2026-10-12	3	\N
1855	1786	missing	annual_physical	65	2026-10-12	3	\N
1856	1787	missing	annual_physical	65	2026-10-12	3	\N
1857	1788	missing	annual_physical	65	2026-10-12	3	\N
1858	1789	missing	annual_physical	65	2026-10-12	3	\N
1859	1790	missing	annual_physical	65	2026-10-12	3	\N
1860	1791	missing	annual_physical	65	2026-10-12	3	\N
1861	1792	missing	annual_physical	65	2026-10-12	3	\N
1862	1793	missing	annual_physical	65	2026-10-12	3	\N
1863	1794	missing	annual_physical	65	2026-10-12	3	\N
1864	1795	missing	annual_physical	65	2026-10-12	3	\N
1865	1796	missing	annual_physical	65	2026-10-12	3	\N
1866	1797	missing	annual_physical	65	2026-10-12	3	\N
1867	1798	missing	annual_physical	65	2026-10-12	3	\N
1868	1799	missing	annual_physical	65	2026-10-12	3	\N
1869	1800	missing	annual_physical	65	2026-10-12	3	\N
1870	1801	missing	annual_physical	65	2026-10-12	3	\N
1871	1802	missing	annual_physical	65	2026-10-12	3	\N
1872	1803	missing	annual_physical	65	2026-10-12	3	\N
1873	1804	missing	annual_physical	65	2026-10-12	3	\N
1874	1805	missing	annual_physical	65	2026-10-12	3	\N
1875	1806	missing	annual_physical	65	2026-10-12	3	\N
1876	1807	missing	annual_physical	65	2026-10-12	3	\N
1877	1808	missing	annual_physical	65	2026-10-12	3	\N
1878	1809	missing	annual_physical	65	2026-10-12	3	\N
1879	1810	missing	annual_physical	65	2026-10-12	3	\N
1880	1811	missing	annual_physical	65	2026-10-12	3	\N
1881	1812	missing	annual_physical	65	2026-10-12	3	\N
1882	1813	missing	annual_physical	65	2026-10-12	3	\N
1883	1814	missing	annual_physical	65	2026-10-12	3	\N
1884	1815	missing	annual_physical	65	2026-10-12	3	\N
1885	1816	missing	annual_physical	65	2026-10-12	3	\N
1886	1817	missing	annual_physical	65	2026-10-12	3	\N
1887	1818	missing	annual_physical	65	2026-10-12	3	\N
1888	1819	missing	annual_physical	65	2026-10-12	3	\N
1889	1820	missing	annual_physical	65	2026-10-12	3	\N
1890	1821	missing	annual_physical	65	2026-10-12	3	\N
1891	1822	missing	annual_physical	65	2026-10-12	3	\N
1892	1823	missing	annual_physical	65	2026-10-12	3	\N
1893	1824	missing	annual_physical	65	2026-10-12	3	\N
1894	1825	missing	annual_physical	65	2026-10-12	3	\N
1895	1826	missing	annual_physical	65	2026-10-12	3	\N
1896	1827	missing	annual_physical	65	2026-10-12	3	\N
1897	1828	missing	annual_physical	65	2026-10-12	3	\N
1898	1829	missing	annual_physical	65	2026-10-12	3	\N
1899	1830	missing	annual_physical	65	2026-10-12	3	\N
1900	1831	missing	annual_physical	65	2026-10-12	3	\N
1901	1832	missing	annual_physical	65	2026-10-12	3	\N
1902	1833	missing	annual_physical	65	2026-10-12	3	\N
1903	1834	missing	annual_physical	65	2026-10-12	3	\N
1904	1835	missing	annual_physical	65	2026-10-12	3	\N
1905	1836	missing	annual_physical	65	2026-10-12	3	\N
1906	1837	missing	annual_physical	65	2026-10-12	3	\N
1907	1838	missing	annual_physical	65	2026-10-12	3	\N
1908	1839	missing	annual_physical	65	2026-10-12	3	\N
1909	1840	missing	annual_physical	65	2026-10-12	3	\N
1910	1841	missing	annual_physical	65	2026-10-12	3	\N
1911	1842	missing	annual_physical	65	2026-10-12	3	\N
1912	1843	missing	annual_physical	65	2026-10-12	3	\N
1913	1844	missing	annual_physical	65	2026-10-12	3	\N
1914	1845	missing	annual_physical	65	2026-10-12	3	\N
1915	1846	missing	annual_physical	65	2026-10-12	3	\N
1916	1847	missing	annual_physical	65	2026-10-12	3	\N
1917	1848	missing	annual_physical	65	2026-10-12	3	\N
1918	1849	missing	annual_physical	65	2026-10-12	3	\N
1919	1850	missing	annual_physical	65	2026-10-12	3	\N
1920	1851	missing	annual_physical	65	2026-10-12	3	\N
1921	1852	missing	annual_physical	65	2026-10-12	3	\N
1922	1853	missing	annual_physical	65	2026-10-12	3	\N
1923	1854	missing	annual_physical	65	2026-10-12	3	\N
1924	1855	missing	annual_physical	65	2026-10-12	3	\N
1925	1856	missing	annual_physical	65	2026-10-12	3	\N
1926	1857	missing	annual_physical	65	2026-10-12	3	\N
1927	1858	missing	annual_physical	65	2026-10-12	3	\N
1928	1859	missing	annual_physical	65	2026-10-12	3	\N
1929	1860	missing	annual_physical	65	2026-10-12	3	\N
1930	1861	missing	annual_physical	65	2026-10-12	3	\N
1931	1862	missing	annual_physical	65	2026-10-12	3	\N
1932	1863	missing	annual_physical	65	2026-10-12	3	\N
1933	1864	missing	annual_physical	65	2026-10-12	3	\N
1934	1865	missing	annual_physical	65	2026-10-12	3	\N
1935	1866	missing	annual_physical	65	2026-10-12	3	\N
1936	1867	missing	annual_physical	65	2026-10-12	3	\N
1937	1868	missing	annual_physical	65	2026-10-12	3	\N
1938	1869	missing	annual_physical	65	2026-10-12	3	\N
1939	1870	missing	annual_physical	65	2026-10-12	3	\N
1940	1871	missing	annual_physical	65	2026-10-12	3	\N
1941	1872	missing	annual_physical	65	2026-10-12	3	\N
1942	1873	missing	annual_physical	65	2026-10-12	3	\N
1943	1874	missing	annual_physical	65	2026-10-12	3	\N
1944	1875	missing	annual_physical	65	2026-10-12	3	\N
1945	1876	missing	annual_physical	65	2026-10-12	3	\N
1946	1877	missing	annual_physical	65	2026-10-12	3	\N
1947	1878	missing	annual_physical	65	2026-10-12	3	\N
1948	1879	missing	annual_physical	65	2026-10-12	3	\N
1949	1880	missing	annual_physical	65	2026-10-12	3	\N
1950	1881	missing	annual_physical	65	2026-10-12	3	\N
1951	1882	missing	annual_physical	65	2026-10-12	3	\N
1952	1883	missing	annual_physical	65	2026-10-12	3	\N
1953	1884	missing	annual_physical	65	2026-10-12	3	\N
1954	1885	missing	annual_physical	65	2026-10-12	3	\N
1955	1886	missing	annual_physical	65	2026-10-12	3	\N
1956	1887	missing	annual_physical	65	2026-10-12	3	\N
1957	1888	missing	annual_physical	65	2026-10-12	3	\N
1958	1889	missing	annual_physical	65	2026-10-12	3	\N
1959	1890	missing	annual_physical	65	2026-10-12	3	\N
1960	1891	missing	annual_physical	65	2026-10-12	3	\N
1961	1892	missing	annual_physical	65	2026-10-12	3	\N
1962	1893	missing	annual_physical	65	2026-10-12	3	\N
1963	1894	missing	annual_physical	65	2026-10-12	3	\N
1964	1895	missing	annual_physical	65	2026-10-12	3	\N
1965	1896	missing	annual_physical	65	2026-10-12	3	\N
1966	1897	missing	annual_physical	65	2026-10-12	3	\N
1967	1898	missing	annual_physical	65	2026-10-12	3	\N
1968	1899	missing	annual_physical	65	2026-10-12	3	\N
1969	1900	missing	annual_physical	65	2026-10-12	3	\N
1970	1901	missing	annual_physical	65	2026-10-12	3	\N
1971	1902	missing	annual_physical	65	2026-10-12	3	\N
1972	1903	missing	annual_physical	65	2026-10-12	3	\N
1973	1904	missing	annual_physical	65	2026-10-12	3	\N
1974	1905	missing	annual_physical	65	2026-10-12	3	\N
1975	1906	missing	annual_physical	65	2026-10-12	3	\N
1976	1907	missing	annual_physical	65	2026-10-12	3	\N
1977	1908	missing	annual_physical	65	2026-10-12	3	\N
1978	1909	missing	annual_physical	65	2026-10-12	3	\N
1979	1910	missing	annual_physical	65	2026-10-12	3	\N
1980	1911	missing	annual_physical	65	2026-10-12	3	\N
1981	1912	missing	annual_physical	65	2026-10-12	3	\N
1982	1913	missing	annual_physical	65	2026-10-12	3	\N
1983	1914	missing	annual_physical	65	2026-10-12	3	\N
1984	1915	missing	annual_physical	65	2026-10-12	3	\N
1985	1916	missing	annual_physical	65	2026-10-12	3	\N
1986	1917	missing	annual_physical	65	2026-10-12	3	\N
1987	1918	missing	annual_physical	65	2026-10-12	3	\N
1988	1919	missing	annual_physical	65	2026-10-12	3	\N
1989	1920	missing	annual_physical	65	2026-10-12	3	\N
1990	1921	missing	annual_physical	65	2026-10-12	3	\N
1991	1922	missing	annual_physical	65	2026-10-12	3	\N
1992	1923	missing	annual_physical	65	2026-10-12	3	\N
1993	1924	missing	annual_physical	65	2026-10-12	3	\N
1994	1925	missing	annual_physical	65	2026-10-12	3	\N
1995	1926	missing	annual_physical	65	2026-10-12	3	\N
1996	1927	missing	annual_physical	65	2026-10-12	3	\N
1997	1928	missing	annual_physical	65	2026-10-12	3	\N
1998	1929	missing	annual_physical	65	2026-10-12	3	\N
1999	1930	missing	annual_physical	65	2026-10-12	3	\N
2000	1931	missing	annual_physical	65	2026-10-12	3	\N
2001	1932	missing	annual_physical	65	2026-10-12	3	\N
2002	1933	missing	annual_physical	65	2026-10-12	3	\N
2003	1934	missing	annual_physical	65	2026-10-12	3	\N
2004	1935	missing	annual_physical	65	2026-10-12	3	\N
2005	1936	missing	annual_physical	65	2026-10-12	3	\N
2006	1937	missing	annual_physical	65	2026-10-12	3	\N
2007	1938	missing	annual_physical	65	2026-10-12	3	\N
2008	1939	missing	annual_physical	65	2026-10-12	3	\N
2009	1940	missing	annual_physical	65	2026-10-12	3	\N
2010	1941	missing	annual_physical	65	2026-10-12	3	\N
2011	1942	missing	annual_physical	65	2026-10-12	3	\N
2012	1943	missing	annual_physical	65	2026-10-12	3	\N
2013	1944	missing	annual_physical	65	2026-10-12	3	\N
2014	1945	missing	annual_physical	65	2026-10-12	3	\N
2015	1946	missing	annual_physical	65	2026-10-12	3	\N
2016	1947	missing	annual_physical	65	2026-10-12	3	\N
2017	1948	missing	annual_physical	65	2026-10-12	3	\N
2018	1949	missing	annual_physical	65	2026-10-12	3	\N
2019	1950	missing	annual_physical	65	2026-10-12	3	\N
2020	1951	missing	annual_physical	65	2026-10-12	3	\N
2021	1952	missing	annual_physical	65	2026-10-12	3	\N
2022	1953	missing	annual_physical	65	2026-10-12	3	\N
2023	1954	missing	annual_physical	65	2026-10-12	3	\N
2024	1955	missing	annual_physical	65	2026-10-12	3	\N
2025	1956	missing	annual_physical	65	2026-10-12	3	\N
2026	1957	missing	annual_physical	65	2026-10-12	3	\N
2027	1958	missing	annual_physical	65	2026-10-12	3	\N
2028	1959	missing	annual_physical	65	2026-10-12	3	\N
2029	1960	missing	annual_physical	65	2026-10-12	3	\N
2030	1961	missing	annual_physical	65	2026-10-12	3	\N
2031	1962	missing	annual_physical	65	2026-10-12	3	\N
2032	1963	missing	annual_physical	65	2026-10-12	3	\N
2033	1964	missing	annual_physical	65	2026-10-12	3	\N
2034	1965	missing	annual_physical	65	2026-10-12	3	\N
2035	1966	missing	annual_physical	65	2026-10-12	3	\N
2036	1967	missing	annual_physical	65	2026-10-12	3	\N
2037	1968	missing	annual_physical	65	2026-10-12	3	\N
2038	1969	missing	annual_physical	65	2026-10-12	3	\N
2039	1970	missing	annual_physical	65	2026-10-12	3	\N
2040	1971	missing	annual_physical	65	2026-10-12	3	\N
2041	1972	missing	annual_physical	65	2026-10-12	3	\N
2042	1973	missing	annual_physical	65	2026-10-12	3	\N
2043	1974	missing	annual_physical	65	2026-10-12	3	\N
2044	1975	missing	annual_physical	65	2026-10-12	3	\N
2045	1976	missing	annual_physical	65	2026-10-12	3	\N
2046	1977	missing	annual_physical	65	2026-10-12	3	\N
2047	1978	missing	annual_physical	65	2026-10-12	3	\N
2048	1979	missing	annual_physical	65	2026-10-12	3	\N
2049	1980	missing	annual_physical	65	2026-10-12	3	\N
2050	1981	missing	annual_physical	65	2026-10-12	3	\N
2051	1982	missing	annual_physical	65	2026-10-12	3	\N
2052	1983	missing	annual_physical	65	2026-10-12	3	\N
2053	1984	missing	annual_physical	65	2026-10-12	3	\N
2054	1985	missing	annual_physical	65	2026-10-12	3	\N
2055	1986	missing	annual_physical	65	2026-10-12	3	\N
2056	1987	missing	annual_physical	65	2026-10-12	3	\N
2057	1988	missing	annual_physical	65	2026-10-12	3	\N
2058	1989	missing	annual_physical	65	2026-10-12	3	\N
2059	1990	missing	annual_physical	65	2026-10-12	3	\N
2060	1991	missing	annual_physical	65	2026-10-12	3	\N
2061	1992	missing	annual_physical	65	2026-10-12	3	\N
2062	1993	missing	annual_physical	65	2026-10-12	3	\N
2063	1994	missing	annual_physical	65	2026-10-12	3	\N
2064	1995	missing	annual_physical	65	2026-10-12	3	\N
2065	1996	missing	annual_physical	65	2026-10-12	3	\N
2066	1997	missing	annual_physical	65	2026-10-12	3	\N
2067	1998	missing	annual_physical	65	2026-10-12	3	\N
2068	1999	missing	annual_physical	65	2026-10-12	3	\N
2069	2000	missing	annual_physical	65	2026-10-12	3	\N
2070	2001	missing	annual_physical	65	2026-10-12	3	\N
2071	2002	missing	annual_physical	65	2026-10-12	3	\N
2072	2003	missing	annual_physical	65	2026-10-12	3	\N
2073	2004	missing	annual_physical	65	2026-10-12	3	\N
2074	2005	missing	annual_physical	65	2026-10-12	3	\N
2075	2006	missing	annual_physical	65	2026-10-12	3	\N
2076	2007	missing	annual_physical	65	2026-10-12	3	\N
2077	2008	missing	annual_physical	65	2026-10-12	3	\N
2078	2009	missing	annual_physical	65	2026-10-12	3	\N
2079	2010	missing	annual_physical	65	2026-10-12	3	\N
2080	2011	missing	annual_physical	65	2026-10-12	3	\N
2081	2012	missing	annual_physical	65	2026-10-12	3	\N
2082	2013	missing	annual_physical	65	2026-10-12	3	\N
2083	2014	borrowed	annual_physical	65	2026-10-12	3	\N
2084	2015	missing	annual_physical	65	2026-10-12	3	\N
2085	2016	missing	annual_physical	65	2026-10-12	3	\N
2086	2017	missing	annual_physical	65	2026-10-12	3	\N
2087	2018	missing	annual_physical	65	2026-10-12	3	\N
2088	2019	missing	annual_physical	65	2026-10-12	3	\N
2089	2020	missing	annual_physical	65	2026-10-12	3	\N
2090	2021	missing	annual_physical	65	2026-10-12	3	\N
2091	2022	missing	annual_physical	65	2026-10-12	3	\N
2092	2023	missing	annual_physical	65	2026-10-12	3	\N
2093	2024	missing	annual_physical	65	2026-10-12	3	\N
2094	2025	missing	annual_physical	65	2026-10-12	3	\N
2095	2026	missing	annual_physical	65	2026-10-12	3	\N
2096	2027	missing	annual_physical	65	2026-10-12	3	\N
2097	2028	borrowed	annual_physical	65	2026-10-12	3	\N
2098	2029	missing	annual_physical	65	2026-10-12	3	\N
2099	2030	missing	annual_physical	65	2026-10-12	3	\N
2100	2031	missing	annual_physical	65	2026-10-12	3	\N
2101	2032	missing	annual_physical	65	2026-10-12	3	\N
2102	2033	missing	annual_physical	65	2026-10-12	3	\N
2103	2034	missing	annual_physical	65	2026-10-12	3	\N
2104	2035	missing	annual_physical	65	2026-10-12	3	\N
2105	2036	missing	annual_physical	65	2026-10-12	3	\N
2106	2037	missing	annual_physical	65	2026-10-12	3	\N
2107	2038	missing	annual_physical	65	2026-10-12	3	\N
2108	2039	missing	annual_physical	65	2026-10-12	3	\N
2109	2040	missing	annual_physical	65	2026-10-12	3	\N
2110	2041	missing	annual_physical	65	2026-10-12	3	\N
2111	2042	missing	annual_physical	65	2026-10-12	3	\N
2112	2043	missing	annual_physical	65	2026-10-12	3	\N
2113	2044	missing	annual_physical	65	2026-10-12	3	\N
2114	2045	missing	annual_physical	65	2026-10-12	3	\N
2115	2046	missing	annual_physical	65	2026-10-12	3	\N
2116	2047	missing	annual_physical	65	2026-10-12	3	\N
2117	2048	missing	annual_physical	65	2026-10-12	3	\N
2118	2049	missing	annual_physical	65	2026-10-12	3	\N
2119	2050	missing	annual_physical	65	2026-10-12	3	\N
2120	2051	missing	annual_physical	65	2026-10-12	3	\N
2121	2052	missing	annual_physical	65	2026-10-12	3	\N
2122	2053	missing	annual_physical	65	2026-10-12	3	\N
2123	2054	missing	annual_physical	65	2026-10-12	3	\N
2124	2055	missing	annual_physical	65	2026-10-12	3	\N
2125	2056	missing	annual_physical	65	2026-10-12	3	\N
2126	2057	missing	annual_physical	65	2026-10-12	3	\N
2127	2058	missing	annual_physical	65	2026-10-12	3	\N
2128	2059	missing	annual_physical	65	2026-10-12	3	\N
2129	2060	missing	annual_physical	65	2026-10-12	3	\N
2130	2061	missing	annual_physical	65	2026-10-12	3	\N
2131	2062	missing	annual_physical	65	2026-10-12	3	\N
2132	2063	missing	annual_physical	65	2026-10-12	3	\N
2133	2064	missing	annual_physical	65	2026-10-12	3	\N
2134	2065	missing	annual_physical	65	2026-10-12	3	\N
2135	2066	missing	annual_physical	65	2026-10-12	3	\N
2136	2067	missing	annual_physical	65	2026-10-12	3	\N
2137	2068	missing	annual_physical	65	2026-10-12	3	\N
2138	2069	missing	annual_physical	65	2026-10-12	3	\N
2139	2070	missing	annual_physical	65	2026-10-12	3	\N
2140	2071	missing	annual_physical	65	2026-10-12	3	\N
2141	2072	missing	annual_physical	65	2026-10-12	3	\N
2142	2073	missing	annual_physical	65	2026-10-12	3	\N
2143	2074	missing	annual_physical	65	2026-10-12	3	\N
2144	2075	missing	annual_physical	65	2026-10-12	3	\N
2145	2076	missing	annual_physical	65	2026-10-12	3	\N
2146	2077	missing	annual_physical	65	2026-10-12	3	\N
2147	2078	missing	annual_physical	65	2026-10-12	3	\N
2148	2079	missing	annual_physical	65	2026-10-12	3	\N
2149	2080	missing	annual_physical	65	2026-10-12	3	\N
2150	2081	missing	annual_physical	65	2026-10-12	3	\N
2151	2082	missing	annual_physical	65	2026-10-12	3	\N
2152	2083	missing	annual_physical	65	2026-10-12	3	\N
2153	2084	missing	annual_physical	65	2026-10-12	3	\N
2154	2085	missing	annual_physical	65	2026-10-12	3	\N
2155	2086	missing	annual_physical	65	2026-10-12	3	\N
2156	2087	missing	annual_physical	65	2026-10-12	3	\N
2157	2088	missing	annual_physical	65	2026-10-12	3	\N
2158	2089	missing	annual_physical	65	2026-10-12	3	\N
2159	2090	missing	annual_physical	65	2026-10-12	3	\N
2160	2091	missing	annual_physical	65	2026-10-12	3	\N
2161	2092	missing	annual_physical	65	2026-10-12	3	\N
2162	2093	missing	annual_physical	65	2026-10-12	3	\N
2163	2094	missing	annual_physical	65	2026-10-12	3	\N
2164	2095	missing	annual_physical	65	2026-10-12	3	\N
2165	2096	missing	annual_physical	65	2026-10-12	3	\N
2166	2097	missing	annual_physical	65	2026-10-12	3	\N
2167	2098	missing	annual_physical	65	2026-10-12	3	\N
2168	2099	missing	annual_physical	65	2026-10-12	3	\N
2169	2100	missing	annual_physical	65	2026-10-12	3	\N
2170	2101	missing	annual_physical	65	2026-10-12	3	\N
2171	2102	missing	annual_physical	65	2026-10-12	3	\N
2172	2103	missing	annual_physical	65	2026-10-12	3	\N
2173	2104	missing	annual_physical	65	2026-10-12	3	\N
2174	2105	missing	annual_physical	65	2026-10-12	3	\N
2175	2106	missing	annual_physical	65	2026-10-12	3	\N
2176	2107	missing	annual_physical	65	2026-10-12	3	\N
2177	2108	missing	annual_physical	65	2026-10-12	3	\N
2178	2109	missing	annual_physical	65	2026-10-12	3	\N
2179	2110	missing	annual_physical	65	2026-10-12	3	\N
2180	2111	missing	annual_physical	65	2026-10-12	3	\N
2181	2112	missing	annual_physical	65	2026-10-12	3	\N
2182	2113	missing	annual_physical	65	2026-10-12	3	\N
2183	2114	missing	annual_physical	65	2026-10-12	3	\N
2184	2115	missing	annual_physical	65	2026-10-12	3	\N
2185	2116	borrowed	annual_physical	65	2026-10-12	3	\N
2186	2117	missing	annual_physical	65	2026-10-12	3	\N
2187	2118	missing	annual_physical	65	2026-10-12	3	\N
2188	2119	missing	annual_physical	65	2026-10-12	3	\N
2189	2120	missing	annual_physical	65	2026-10-12	3	\N
2190	2121	missing	annual_physical	65	2026-10-12	3	\N
2191	2122	missing	annual_physical	65	2026-10-12	3	\N
2192	2123	missing	annual_physical	65	2026-10-12	3	\N
2193	2124	missing	annual_physical	65	2026-10-12	3	\N
2194	2125	missing	annual_physical	65	2026-10-12	3	\N
2195	2126	missing	annual_physical	65	2026-10-12	3	\N
2196	2127	missing	annual_physical	65	2026-10-12	3	\N
2197	2128	missing	annual_physical	65	2026-10-12	3	\N
2198	2129	missing	annual_physical	65	2026-10-12	3	\N
2199	2130	missing	annual_physical	65	2026-10-12	3	\N
2200	2131	missing	annual_physical	65	2026-10-12	3	\N
2201	2132	missing	annual_physical	65	2026-10-12	3	\N
2202	2133	missing	annual_physical	65	2026-10-12	3	\N
2203	2134	missing	annual_physical	65	2026-10-12	3	\N
2204	2135	missing	annual_physical	65	2026-10-12	3	\N
2205	2136	missing	annual_physical	65	2026-10-12	3	\N
2206	2137	missing	annual_physical	65	2026-10-12	3	\N
2207	2138	missing	annual_physical	65	2026-10-12	3	\N
2208	2139	missing	annual_physical	65	2026-10-12	3	\N
2209	2140	missing	annual_physical	65	2026-10-12	3	\N
2210	2141	missing	annual_physical	65	2026-10-12	3	\N
2211	2142	missing	annual_physical	65	2026-10-12	3	\N
2212	2143	missing	annual_physical	65	2026-10-12	3	\N
2213	2144	missing	annual_physical	65	2026-10-12	3	\N
2214	2145	missing	annual_physical	65	2026-10-12	3	\N
2215	2146	missing	annual_physical	65	2026-10-12	3	\N
2216	2147	missing	annual_physical	65	2026-10-12	3	\N
2217	2148	missing	annual_physical	65	2026-10-12	3	\N
2218	2149	missing	annual_physical	65	2026-10-12	3	\N
2219	2150	missing	annual_physical	65	2026-10-12	3	\N
2220	2151	missing	annual_physical	65	2026-10-12	3	\N
2221	2152	missing	annual_physical	65	2026-10-12	3	\N
2222	2153	missing	annual_physical	65	2026-10-12	3	\N
2223	2154	missing	annual_physical	65	2026-10-12	3	\N
2224	2155	missing	annual_physical	65	2026-10-12	3	\N
2225	2156	missing	annual_physical	65	2026-10-12	3	\N
2226	2157	missing	annual_physical	65	2026-10-12	3	\N
2227	2158	missing	annual_physical	65	2026-10-12	3	\N
2228	2159	missing	annual_physical	65	2026-10-12	3	\N
2229	2160	missing	annual_physical	65	2026-10-12	3	\N
2230	2161	missing	annual_physical	65	2026-10-12	3	\N
2231	2162	missing	annual_physical	65	2026-10-12	3	\N
2232	2163	missing	annual_physical	65	2026-10-12	3	\N
2233	2164	missing	annual_physical	65	2026-10-12	3	\N
2234	2165	missing	annual_physical	65	2026-10-12	3	\N
2235	2166	missing	annual_physical	65	2026-10-12	3	\N
2236	2167	missing	annual_physical	65	2026-10-12	3	\N
2237	2168	missing	annual_physical	65	2026-10-12	3	\N
2238	2169	missing	annual_physical	65	2026-10-12	3	\N
2239	2170	missing	annual_physical	65	2026-10-12	3	\N
2240	2171	missing	annual_physical	65	2026-10-12	3	\N
2241	2172	missing	annual_physical	65	2026-10-12	3	\N
2242	2173	missing	annual_physical	65	2026-10-12	3	\N
2243	2174	missing	annual_physical	65	2026-10-12	3	\N
2244	2175	missing	annual_physical	65	2026-10-12	3	\N
2245	2176	missing	annual_physical	65	2026-10-12	3	\N
2246	2177	missing	annual_physical	65	2026-10-12	3	\N
2247	2178	missing	annual_physical	65	2026-10-12	3	\N
2248	2179	missing	annual_physical	65	2026-10-12	3	\N
2249	2180	missing	annual_physical	65	2026-10-12	3	\N
2250	2181	missing	annual_physical	65	2026-10-12	3	\N
2251	2182	missing	annual_physical	65	2026-10-12	3	\N
2252	2183	missing	annual_physical	65	2026-10-12	3	\N
2253	2184	missing	annual_physical	65	2026-10-12	3	\N
2254	2185	missing	annual_physical	65	2026-10-12	3	\N
2255	2186	missing	annual_physical	65	2026-10-12	3	\N
2256	2187	missing	annual_physical	65	2026-10-12	3	\N
2257	2188	missing	annual_physical	65	2026-10-12	3	\N
2258	2189	missing	annual_physical	65	2026-10-12	3	\N
2259	2190	missing	annual_physical	65	2026-10-12	3	\N
2260	2191	missing	annual_physical	65	2026-10-12	3	\N
2261	2192	missing	annual_physical	65	2026-10-12	3	\N
2262	2193	missing	annual_physical	65	2026-10-12	3	\N
2263	2194	missing	annual_physical	65	2026-10-12	3	\N
2264	2195	missing	annual_physical	65	2026-10-12	3	\N
2265	2196	missing	annual_physical	65	2026-10-12	3	\N
2266	2197	missing	annual_physical	65	2026-10-12	3	\N
2267	2198	missing	annual_physical	65	2026-10-12	3	\N
2268	2199	missing	annual_physical	65	2026-10-12	3	\N
2269	2200	missing	annual_physical	65	2026-10-12	3	\N
2270	2201	missing	annual_physical	65	2026-10-12	3	\N
2271	2202	missing	annual_physical	65	2026-10-12	3	\N
2272	2203	missing	annual_physical	65	2026-10-12	3	\N
2273	2204	missing	annual_physical	65	2026-10-12	3	\N
2274	2205	missing	annual_physical	65	2026-10-12	3	\N
2275	2206	missing	annual_physical	65	2026-10-12	3	\N
2276	2207	missing	annual_physical	65	2026-10-12	3	\N
2277	2208	missing	annual_physical	65	2026-10-12	3	\N
2278	2209	missing	annual_physical	65	2026-10-12	3	\N
2279	2210	missing	annual_physical	65	2026-10-12	3	\N
2280	2211	missing	annual_physical	65	2026-10-12	3	\N
2281	2212	missing	annual_physical	65	2026-10-12	3	\N
2282	2213	missing	annual_physical	65	2026-10-12	3	\N
2283	2214	missing	annual_physical	65	2026-10-12	3	\N
2284	2215	missing	annual_physical	65	2026-10-12	3	\N
2285	2216	missing	annual_physical	65	2026-10-12	3	\N
2286	2217	missing	annual_physical	65	2026-10-12	3	\N
2287	2218	missing	annual_physical	65	2026-10-12	3	\N
2288	2219	missing	annual_physical	65	2026-10-12	3	\N
2289	2220	missing	annual_physical	65	2026-10-12	3	\N
2290	2221	missing	annual_physical	65	2026-10-12	3	\N
2291	2222	missing	annual_physical	65	2026-10-12	3	\N
2292	2223	missing	annual_physical	65	2026-10-12	3	\N
2293	2224	missing	annual_physical	65	2026-10-12	3	\N
2294	2225	missing	annual_physical	65	2026-10-12	3	\N
2295	2226	missing	annual_physical	65	2026-10-12	3	\N
2296	2227	missing	annual_physical	65	2026-10-12	3	\N
2297	2228	missing	annual_physical	65	2026-10-12	3	\N
2298	2229	missing	annual_physical	65	2026-10-12	3	\N
2299	2230	missing	annual_physical	65	2026-10-12	3	\N
2300	2231	missing	annual_physical	65	2026-10-12	3	\N
2301	2232	missing	annual_physical	65	2026-10-12	3	\N
2302	2233	missing	annual_physical	65	2026-10-12	3	\N
2303	2234	missing	annual_physical	65	2026-10-12	3	\N
2304	2235	missing	annual_physical	65	2026-10-12	3	\N
2305	2236	missing	annual_physical	65	2026-10-12	3	\N
2306	2237	missing	annual_physical	65	2026-10-12	3	\N
2307	2238	missing	annual_physical	65	2026-10-12	3	\N
2308	2239	missing	annual_physical	65	2026-10-12	3	\N
2309	2240	missing	annual_physical	65	2026-10-12	3	\N
2310	2241	missing	annual_physical	65	2026-10-12	3	\N
2311	2242	missing	annual_physical	65	2026-10-12	3	\N
2312	2243	missing	annual_physical	65	2026-10-12	3	\N
2313	2244	missing	annual_physical	65	2026-10-12	3	\N
2314	2245	missing	annual_physical	65	2026-10-12	3	\N
2315	2246	missing	annual_physical	65	2026-10-12	3	\N
2316	2247	missing	annual_physical	65	2026-10-12	3	\N
2317	2248	missing	annual_physical	65	2026-10-12	3	\N
2318	2249	missing	annual_physical	65	2026-10-12	3	\N
2319	2250	missing	annual_physical	65	2026-10-12	3	\N
2320	2251	missing	annual_physical	65	2026-10-12	3	\N
2321	2252	missing	annual_physical	65	2026-10-12	3	\N
2322	2253	missing	annual_physical	65	2026-10-12	3	\N
2323	2254	missing	annual_physical	65	2026-10-12	3	\N
2324	2255	missing	annual_physical	65	2026-10-12	3	\N
2325	2256	missing	annual_physical	65	2026-10-12	3	\N
2326	2257	missing	annual_physical	65	2026-10-12	3	\N
2327	2258	missing	annual_physical	65	2026-10-12	3	\N
2328	2259	missing	annual_physical	65	2026-10-12	3	\N
2329	2260	missing	annual_physical	65	2026-10-12	3	\N
2330	2261	missing	annual_physical	65	2026-10-12	3	\N
2331	2262	missing	annual_physical	65	2026-10-12	3	\N
2332	2263	missing	annual_physical	65	2026-10-12	3	\N
2333	2264	missing	annual_physical	65	2026-10-12	3	\N
2334	2265	missing	annual_physical	65	2026-10-12	3	\N
2335	2266	missing	annual_physical	65	2026-10-12	3	\N
2336	2267	missing	annual_physical	65	2026-10-12	3	\N
2337	2268	missing	annual_physical	65	2026-10-12	3	\N
2338	2269	missing	annual_physical	65	2026-10-12	3	\N
2339	2270	missing	annual_physical	65	2026-10-12	3	\N
2340	2271	missing	annual_physical	65	2026-10-12	3	\N
2341	2272	missing	annual_physical	65	2026-10-12	3	\N
2342	2273	missing	annual_physical	65	2026-10-12	3	\N
2343	2274	missing	annual_physical	65	2026-10-12	3	\N
2344	2275	missing	annual_physical	65	2026-10-12	3	\N
2345	2276	missing	annual_physical	65	2026-10-12	3	\N
2346	2277	missing	annual_physical	65	2026-10-12	3	\N
2347	2278	missing	annual_physical	65	2026-10-12	3	\N
2348	2279	missing	annual_physical	65	2026-10-12	3	\N
2349	2280	missing	annual_physical	65	2026-10-12	3	\N
2350	2281	missing	annual_physical	65	2026-10-12	3	\N
2351	2282	missing	annual_physical	65	2026-10-12	3	\N
2352	2283	missing	annual_physical	65	2026-10-12	3	\N
2353	2284	missing	annual_physical	65	2026-10-12	3	\N
2354	2285	missing	annual_physical	65	2026-10-12	3	\N
2355	2286	missing	annual_physical	65	2026-10-12	3	\N
2356	2287	missing	annual_physical	65	2026-10-12	3	\N
2357	2288	missing	annual_physical	65	2026-10-12	3	\N
2358	2289	missing	annual_physical	65	2026-10-12	3	\N
2359	2290	missing	annual_physical	65	2026-10-12	3	\N
2360	2291	missing	annual_physical	65	2026-10-12	3	\N
2361	2292	missing	annual_physical	65	2026-10-12	3	\N
2362	2293	missing	annual_physical	65	2026-10-12	3	\N
2363	2294	missing	annual_physical	65	2026-10-12	3	\N
2364	2295	missing	annual_physical	65	2026-10-12	3	\N
2365	2296	missing	annual_physical	65	2026-10-12	3	\N
2366	2297	missing	annual_physical	65	2026-10-12	3	\N
2367	2298	missing	annual_physical	65	2026-10-12	3	\N
2368	2299	missing	annual_physical	65	2026-10-12	3	\N
2369	2300	missing	annual_physical	65	2026-10-12	3	\N
2370	2301	missing	annual_physical	65	2026-10-12	3	\N
2371	2302	missing	annual_physical	65	2026-10-12	3	\N
2372	2303	missing	annual_physical	65	2026-10-12	3	\N
2373	2304	missing	annual_physical	65	2026-10-12	3	\N
2374	2305	missing	annual_physical	65	2026-10-12	3	\N
2375	2306	missing	annual_physical	65	2026-10-12	3	\N
2376	2307	missing	annual_physical	65	2026-10-12	3	\N
2377	2308	missing	annual_physical	65	2026-10-12	3	\N
2378	2309	missing	annual_physical	65	2026-10-12	3	\N
2379	2310	missing	annual_physical	65	2026-10-12	3	\N
2380	2311	missing	annual_physical	65	2026-10-12	3	\N
2381	2312	missing	annual_physical	65	2026-10-12	3	\N
2382	2313	missing	annual_physical	65	2026-10-12	3	\N
2383	2314	missing	annual_physical	65	2026-10-12	3	\N
2384	2315	missing	annual_physical	65	2026-10-12	3	\N
2385	2316	missing	annual_physical	65	2026-10-12	3	\N
2386	2317	missing	annual_physical	65	2026-10-12	3	\N
2387	2318	missing	annual_physical	65	2026-10-12	3	\N
2388	2319	missing	annual_physical	65	2026-10-12	3	\N
2389	2320	missing	annual_physical	65	2026-10-12	3	\N
2390	2321	missing	annual_physical	65	2026-10-12	3	\N
2391	2322	missing	annual_physical	65	2026-10-12	3	\N
2392	2323	missing	annual_physical	65	2026-10-12	3	\N
2393	2324	missing	annual_physical	65	2026-10-12	3	\N
2394	2325	missing	annual_physical	65	2026-10-12	3	\N
2395	2326	missing	annual_physical	65	2026-10-12	3	\N
2396	2327	missing	annual_physical	65	2026-10-12	3	\N
2397	2328	missing	annual_physical	65	2026-10-12	3	\N
2398	2329	missing	annual_physical	65	2026-10-12	3	\N
2399	2330	missing	annual_physical	65	2026-10-12	3	\N
2400	2331	missing	annual_physical	65	2026-10-12	3	\N
2401	2332	missing	annual_physical	65	2026-10-12	3	\N
2402	2333	missing	annual_physical	65	2026-10-12	3	\N
2403	2334	missing	annual_physical	65	2026-10-12	3	\N
2404	2335	missing	annual_physical	65	2026-10-12	3	\N
2405	2336	missing	annual_physical	65	2026-10-12	3	\N
2406	2337	missing	annual_physical	65	2026-10-12	3	\N
2407	2338	missing	annual_physical	65	2026-10-12	3	\N
2408	2339	missing	annual_physical	65	2026-10-12	3	\N
2409	2340	missing	annual_physical	65	2026-10-12	3	\N
2410	2341	missing	annual_physical	65	2026-10-12	3	\N
2411	2342	missing	annual_physical	65	2026-10-12	3	\N
2412	2343	missing	annual_physical	65	2026-10-12	3	\N
2413	2344	missing	annual_physical	65	2026-10-12	3	\N
2414	2345	missing	annual_physical	65	2026-10-12	3	\N
2415	2346	missing	annual_physical	65	2026-10-12	3	\N
2416	2347	missing	annual_physical	65	2026-10-12	3	\N
2417	2348	missing	annual_physical	65	2026-10-12	3	\N
2418	2349	missing	annual_physical	65	2026-10-12	3	\N
2419	2350	missing	annual_physical	65	2026-10-12	3	\N
2420	2351	missing	annual_physical	65	2026-10-12	3	\N
2421	2352	missing	annual_physical	65	2026-10-12	3	\N
2422	2353	missing	annual_physical	65	2026-10-12	3	\N
2423	2354	missing	annual_physical	65	2026-10-12	3	\N
2424	2355	missing	annual_physical	65	2026-10-12	3	\N
2425	2356	missing	annual_physical	65	2026-10-12	3	\N
2426	2357	missing	annual_physical	65	2026-10-12	3	\N
2427	2358	missing	annual_physical	65	2026-10-12	3	\N
2428	2359	missing	annual_physical	65	2026-10-12	3	\N
2429	2360	missing	annual_physical	65	2026-10-12	3	\N
2430	2361	missing	annual_physical	65	2026-10-12	3	\N
2431	2362	missing	annual_physical	65	2026-10-12	3	\N
2432	2363	missing	annual_physical	65	2026-10-12	3	\N
2433	2364	missing	annual_physical	65	2026-10-12	3	\N
2434	2365	missing	annual_physical	65	2026-10-12	3	\N
2435	2366	missing	annual_physical	65	2026-10-12	3	\N
2436	2367	missing	annual_physical	65	2026-10-12	3	\N
2437	2368	missing	annual_physical	65	2026-10-12	3	\N
2438	2369	missing	annual_physical	65	2026-10-12	3	\N
2439	2370	missing	annual_physical	65	2026-10-12	3	\N
2440	2371	missing	annual_physical	65	2026-10-12	3	\N
2441	2372	missing	annual_physical	65	2026-10-12	3	\N
2442	2373	missing	annual_physical	65	2026-10-12	3	\N
2443	2374	missing	annual_physical	65	2026-10-12	3	\N
2444	2375	missing	annual_physical	65	2026-10-12	3	\N
2445	2376	missing	annual_physical	65	2026-10-12	3	\N
2446	2377	missing	annual_physical	65	2026-10-12	3	\N
2447	2378	missing	annual_physical	65	2026-10-12	3	\N
2448	2379	missing	annual_physical	65	2026-10-12	3	\N
2449	2380	missing	annual_physical	65	2026-10-12	3	\N
2450	2381	missing	annual_physical	65	2026-10-12	3	\N
2451	2382	missing	annual_physical	65	2026-10-12	3	\N
2452	2383	missing	annual_physical	65	2026-10-12	3	\N
2453	2384	missing	annual_physical	65	2026-10-12	3	\N
2454	2385	missing	annual_physical	65	2026-10-12	3	\N
2455	2386	missing	annual_physical	65	2026-10-12	3	\N
2456	2387	missing	annual_physical	65	2026-10-12	3	\N
2457	2388	missing	annual_physical	65	2026-10-12	3	\N
2458	2389	missing	annual_physical	65	2026-10-12	3	\N
2459	2390	missing	annual_physical	65	2026-10-12	3	\N
2460	2391	missing	annual_physical	65	2026-10-12	3	\N
2461	2392	missing	annual_physical	65	2026-10-12	3	\N
2462	2393	missing	annual_physical	65	2026-10-12	3	\N
2463	2394	missing	annual_physical	65	2026-10-12	3	\N
2464	2395	missing	annual_physical	65	2026-10-12	3	\N
2465	2396	missing	annual_physical	65	2026-10-12	3	\N
2466	2397	missing	annual_physical	65	2026-10-12	3	\N
2467	2398	missing	annual_physical	65	2026-10-12	3	\N
2468	2399	missing	annual_physical	65	2026-10-12	3	\N
2469	2400	missing	annual_physical	65	2026-10-12	3	\N
2470	2401	missing	annual_physical	65	2026-10-12	3	\N
2471	2402	missing	annual_physical	65	2026-10-12	3	\N
2472	2403	missing	annual_physical	65	2026-10-12	3	\N
2473	2404	missing	annual_physical	65	2026-10-12	3	\N
2474	2405	missing	annual_physical	65	2026-10-12	3	\N
2475	2406	missing	annual_physical	65	2026-10-12	3	\N
2476	2407	missing	annual_physical	65	2026-10-12	3	\N
2477	2408	missing	annual_physical	65	2026-10-12	3	\N
2478	2409	missing	annual_physical	65	2026-10-12	3	\N
2479	2410	missing	annual_physical	65	2026-10-12	3	\N
2480	2411	missing	annual_physical	65	2026-10-12	3	\N
2481	2412	missing	annual_physical	65	2026-10-12	3	\N
2482	2413	missing	annual_physical	65	2026-10-12	3	\N
2483	2414	missing	annual_physical	65	2026-10-12	3	\N
2484	2415	missing	annual_physical	65	2026-10-12	3	\N
2485	2416	missing	annual_physical	65	2026-10-12	3	\N
2486	2417	missing	annual_physical	65	2026-10-12	3	\N
2487	2418	missing	annual_physical	65	2026-10-12	3	\N
2488	2419	missing	annual_physical	65	2026-10-12	3	\N
2489	2420	missing	annual_physical	65	2026-10-12	3	\N
2490	2421	missing	annual_physical	65	2026-10-12	3	\N
2491	2422	missing	annual_physical	65	2026-10-12	3	\N
2492	2423	missing	annual_physical	65	2026-10-12	3	\N
2493	2424	missing	annual_physical	65	2026-10-12	3	\N
2494	2425	missing	annual_physical	65	2026-10-12	3	\N
2495	2426	missing	annual_physical	65	2026-10-12	3	\N
2496	2427	missing	annual_physical	65	2026-10-12	3	\N
2497	2428	missing	annual_physical	65	2026-10-12	3	\N
2498	2429	missing	annual_physical	65	2026-10-12	3	\N
2499	2430	missing	annual_physical	65	2026-10-12	3	\N
2500	2431	missing	annual_physical	65	2026-10-12	3	\N
2501	2432	missing	annual_physical	65	2026-10-12	3	\N
2502	2433	missing	annual_physical	65	2026-10-12	3	\N
2503	2434	missing	annual_physical	65	2026-10-12	3	\N
2504	2435	missing	annual_physical	65	2026-10-12	3	\N
2505	2436	missing	annual_physical	65	2026-10-12	3	\N
2506	2437	missing	annual_physical	65	2026-10-12	3	\N
2507	2438	missing	annual_physical	65	2026-10-12	3	\N
2508	2439	missing	annual_physical	65	2026-10-12	3	\N
2509	2440	missing	annual_physical	65	2026-10-12	3	\N
2510	2441	missing	annual_physical	65	2026-10-12	3	\N
2511	2442	missing	annual_physical	65	2026-10-12	3	\N
2512	2443	missing	annual_physical	65	2026-10-12	3	\N
2513	2444	missing	annual_physical	65	2026-10-12	3	\N
2514	2445	missing	annual_physical	65	2026-10-12	3	\N
2515	2446	missing	annual_physical	65	2026-10-12	3	\N
2516	2447	missing	annual_physical	65	2026-10-12	3	\N
2517	2448	missing	annual_physical	65	2026-10-12	3	\N
2518	2449	missing	annual_physical	65	2026-10-12	3	\N
2519	2450	missing	annual_physical	65	2026-10-12	3	\N
2520	2451	missing	annual_physical	65	2026-10-12	3	\N
2521	2452	missing	annual_physical	65	2026-10-12	3	\N
2522	2453	missing	annual_physical	65	2026-10-12	3	\N
2523	2454	missing	annual_physical	65	2026-10-12	3	\N
2524	2455	missing	annual_physical	65	2026-10-12	3	\N
2525	2456	missing	annual_physical	65	2026-10-12	3	\N
2526	2457	missing	annual_physical	65	2026-10-12	3	\N
2527	2458	missing	annual_physical	65	2026-10-12	3	\N
2528	2459	missing	annual_physical	65	2026-10-12	3	\N
2529	2460	missing	annual_physical	65	2026-10-12	3	\N
2530	2461	missing	annual_physical	65	2026-10-12	3	\N
2531	2462	missing	annual_physical	65	2026-10-12	3	\N
2532	2463	missing	annual_physical	65	2026-10-12	3	\N
2533	2464	missing	annual_physical	65	2026-10-12	3	\N
2534	2465	missing	annual_physical	65	2026-10-12	3	\N
2535	2466	missing	annual_physical	65	2026-10-12	3	\N
2536	2467	missing	annual_physical	65	2026-10-12	3	\N
2537	2468	missing	annual_physical	65	2026-10-12	3	\N
2538	2469	missing	annual_physical	65	2026-10-12	3	\N
2539	2470	missing	annual_physical	65	2026-10-12	3	\N
2540	2471	missing	annual_physical	65	2026-10-12	3	\N
2541	2472	missing	annual_physical	65	2026-10-12	3	\N
2542	2473	missing	annual_physical	65	2026-10-12	3	\N
2543	2474	missing	annual_physical	65	2026-10-12	3	\N
2544	2475	missing	annual_physical	65	2026-10-12	3	\N
2545	2476	missing	annual_physical	65	2026-10-12	3	\N
2546	2477	missing	annual_physical	65	2026-10-12	3	\N
2547	2478	missing	annual_physical	65	2026-10-12	3	\N
2548	2479	missing	annual_physical	65	2026-10-12	3	\N
2549	2480	missing	annual_physical	65	2026-10-12	3	\N
2550	2481	missing	annual_physical	65	2026-10-12	3	\N
2551	2482	missing	annual_physical	65	2026-10-12	3	\N
2552	2483	missing	annual_physical	65	2026-10-12	3	\N
2553	2484	missing	annual_physical	65	2026-10-12	3	\N
2554	2485	missing	annual_physical	65	2026-10-12	3	\N
2555	2486	missing	annual_physical	65	2026-10-12	3	\N
2556	2487	missing	annual_physical	65	2026-10-12	3	\N
2557	2488	missing	annual_physical	65	2026-10-12	3	\N
2558	2489	missing	annual_physical	65	2026-10-12	3	\N
2559	2490	missing	annual_physical	65	2026-10-12	3	\N
2560	2491	missing	annual_physical	65	2026-10-12	3	\N
2561	2492	missing	annual_physical	65	2026-10-12	3	\N
2562	2493	missing	annual_physical	65	2026-10-12	3	\N
2563	2494	missing	annual_physical	65	2026-10-12	3	\N
2564	2495	missing	annual_physical	65	2026-10-12	3	\N
2565	2496	missing	annual_physical	65	2026-10-12	3	\N
2566	2497	missing	annual_physical	65	2026-10-12	3	\N
2567	2498	missing	annual_physical	65	2026-10-12	3	\N
2568	2499	missing	annual_physical	65	2026-10-12	3	\N
2569	2500	missing	annual_physical	65	2026-10-12	3	\N
2570	2501	missing	annual_physical	65	2026-10-12	3	\N
2571	2502	missing	annual_physical	65	2026-10-12	3	\N
2572	2503	missing	annual_physical	65	2026-10-12	3	\N
2573	2504	missing	annual_physical	65	2026-10-12	3	\N
2574	2505	missing	annual_physical	65	2026-10-12	3	\N
2575	2506	missing	annual_physical	65	2026-10-12	3	\N
2576	2507	missing	annual_physical	65	2026-10-12	3	\N
2577	2508	missing	annual_physical	65	2026-10-12	3	\N
2578	2509	missing	annual_physical	65	2026-10-12	3	\N
2579	2510	missing	annual_physical	65	2026-10-12	3	\N
2580	2511	missing	annual_physical	65	2026-10-12	3	\N
2581	2512	missing	annual_physical	65	2026-10-12	3	\N
2582	2513	missing	annual_physical	65	2026-10-12	3	\N
2583	2514	missing	annual_physical	65	2026-10-12	3	\N
2584	2515	missing	annual_physical	65	2026-10-12	3	\N
2585	2516	missing	annual_physical	65	2026-10-12	3	\N
2586	2517	missing	annual_physical	65	2026-10-12	3	\N
2587	2518	missing	annual_physical	65	2026-10-12	3	\N
2588	2519	missing	annual_physical	65	2026-10-12	3	\N
2589	2520	missing	annual_physical	65	2026-10-12	3	\N
2590	2521	missing	annual_physical	65	2026-10-12	3	\N
2591	2522	missing	annual_physical	65	2026-10-12	3	\N
2592	2523	missing	annual_physical	65	2026-10-12	3	\N
2593	2524	missing	annual_physical	65	2026-10-12	3	\N
2594	2525	missing	annual_physical	65	2026-10-12	3	\N
2595	2526	missing	annual_physical	65	2026-10-12	3	\N
2596	2527	missing	annual_physical	65	2026-10-12	3	\N
2597	2528	missing	annual_physical	65	2026-10-12	3	\N
2598	2529	missing	annual_physical	65	2026-10-12	3	\N
2599	2530	missing	annual_physical	65	2026-10-12	3	\N
2600	2531	missing	annual_physical	65	2026-10-12	3	\N
2601	2532	missing	annual_physical	65	2026-10-12	3	\N
2602	2533	missing	annual_physical	65	2026-10-12	3	\N
2603	2534	missing	annual_physical	65	2026-10-12	3	\N
2604	2535	missing	annual_physical	65	2026-10-12	3	\N
2605	2536	missing	annual_physical	65	2026-10-12	3	\N
2606	2537	missing	annual_physical	65	2026-10-12	3	\N
2607	2538	missing	annual_physical	65	2026-10-12	3	\N
2608	2539	missing	annual_physical	65	2026-10-12	3	\N
2609	2540	missing	annual_physical	65	2026-10-12	3	\N
2610	2541	missing	annual_physical	65	2026-10-12	3	\N
2611	2542	missing	annual_physical	65	2026-10-12	3	\N
2612	2543	missing	annual_physical	65	2026-10-12	3	\N
2613	2544	missing	annual_physical	65	2026-10-12	3	\N
2614	2545	missing	annual_physical	65	2026-10-12	3	\N
2615	2546	missing	annual_physical	65	2026-10-12	3	\N
2616	2547	missing	annual_physical	65	2026-10-12	3	\N
2617	2548	missing	annual_physical	65	2026-10-12	3	\N
2618	2549	missing	annual_physical	65	2026-10-12	3	\N
2619	2550	borrowed	annual_physical	65	2026-10-12	3	\N
2620	2551	missing	annual_physical	65	2026-10-12	3	\N
2621	2552	missing	annual_physical	65	2026-10-12	3	\N
2622	2553	missing	annual_physical	65	2026-10-12	3	\N
2623	2554	missing	annual_physical	65	2026-10-12	3	\N
2624	2555	missing	annual_physical	65	2026-10-12	3	\N
2625	2556	missing	annual_physical	65	2026-10-12	3	\N
2626	2557	missing	annual_physical	65	2026-10-12	3	\N
2627	2558	missing	annual_physical	65	2026-10-12	3	\N
2628	2559	missing	annual_physical	65	2026-10-12	3	\N
2629	2560	missing	annual_physical	65	2026-10-12	3	\N
2630	2561	missing	annual_physical	65	2026-10-12	3	\N
2631	2562	missing	annual_physical	65	2026-10-12	3	\N
2632	2563	missing	annual_physical	65	2026-10-12	3	\N
2633	2564	missing	annual_physical	65	2026-10-12	3	\N
2634	2565	missing	annual_physical	65	2026-10-12	3	\N
2635	2566	missing	annual_physical	65	2026-10-12	3	\N
2636	2567	missing	annual_physical	65	2026-10-12	3	\N
2637	2568	missing	annual_physical	65	2026-10-12	3	\N
2638	2569	missing	annual_physical	65	2026-10-12	3	\N
2639	2570	missing	annual_physical	65	2026-10-12	3	\N
2640	2571	missing	annual_physical	65	2026-10-12	3	\N
2641	2572	missing	annual_physical	65	2026-10-12	3	\N
2642	2573	missing	annual_physical	65	2026-10-12	3	\N
2643	2574	missing	annual_physical	65	2026-10-12	3	\N
2644	2575	missing	annual_physical	65	2026-10-12	3	\N
2645	2576	missing	annual_physical	65	2026-10-12	3	\N
2646	2577	missing	annual_physical	65	2026-10-12	3	\N
2647	2578	missing	annual_physical	65	2026-10-12	3	\N
2648	2579	missing	annual_physical	65	2026-10-12	3	\N
2649	2580	missing	annual_physical	65	2026-10-12	3	\N
2650	2581	missing	annual_physical	65	2026-10-12	3	\N
2651	2582	missing	annual_physical	65	2026-10-12	3	\N
2652	2583	missing	annual_physical	65	2026-10-12	3	\N
2653	2584	missing	annual_physical	65	2026-10-12	3	\N
2654	2585	missing	annual_physical	65	2026-10-12	3	\N
2655	2586	missing	annual_physical	65	2026-10-12	3	\N
2656	2587	missing	annual_physical	65	2026-10-12	3	\N
2657	2588	missing	annual_physical	65	2026-10-12	3	\N
2658	2589	missing	annual_physical	65	2026-10-12	3	\N
2659	2590	missing	annual_physical	65	2026-10-12	3	\N
2660	2591	missing	annual_physical	65	2026-10-12	3	\N
2661	2592	missing	annual_physical	65	2026-10-12	3	\N
2662	2593	missing	annual_physical	65	2026-10-12	3	\N
2663	2594	missing	annual_physical	65	2026-10-12	3	\N
2664	2595	missing	annual_physical	65	2026-10-12	3	\N
2665	2596	missing	annual_physical	65	2026-10-12	3	\N
2666	2597	missing	annual_physical	65	2026-10-12	3	\N
2667	2598	missing	annual_physical	65	2026-10-12	3	\N
2668	2599	missing	annual_physical	65	2026-10-12	3	\N
2669	2600	missing	annual_physical	65	2026-10-12	3	\N
2670	2601	missing	annual_physical	65	2026-10-12	3	\N
2671	2602	missing	annual_physical	65	2026-10-12	3	\N
2672	2603	missing	annual_physical	65	2026-10-12	3	\N
2673	2604	missing	annual_physical	65	2026-10-12	3	\N
2674	2605	missing	annual_physical	65	2026-10-12	3	\N
2675	2606	missing	annual_physical	65	2026-10-12	3	\N
2676	2607	missing	annual_physical	65	2026-10-12	3	\N
2677	2608	missing	annual_physical	65	2026-10-12	3	\N
2678	2609	missing	annual_physical	65	2026-10-12	3	\N
2679	2610	missing	annual_physical	65	2026-10-12	3	\N
2680	2611	missing	annual_physical	65	2026-10-12	3	\N
2681	2612	missing	annual_physical	65	2026-10-12	3	\N
2682	2613	missing	annual_physical	65	2026-10-12	3	\N
2683	2614	missing	annual_physical	65	2026-10-12	3	\N
2684	2615	missing	annual_physical	65	2026-10-12	3	\N
2685	2616	missing	annual_physical	65	2026-10-12	3	\N
2686	2617	missing	annual_physical	65	2026-10-12	3	\N
2687	2618	missing	annual_physical	65	2026-10-12	3	\N
2688	2619	missing	annual_physical	65	2026-10-12	3	\N
2689	2620	missing	annual_physical	65	2026-10-12	3	\N
2690	2621	missing	annual_physical	65	2026-10-12	3	\N
2691	2622	missing	annual_physical	65	2026-10-12	3	\N
2692	2623	missing	annual_physical	65	2026-10-12	3	\N
2693	2624	missing	annual_physical	65	2026-10-12	3	\N
2694	2625	missing	annual_physical	65	2026-10-12	3	\N
2695	2626	missing	annual_physical	65	2026-10-12	3	\N
2696	2627	missing	annual_physical	65	2026-10-12	3	\N
2697	2628	missing	annual_physical	65	2026-10-12	3	\N
2698	2629	missing	annual_physical	65	2026-10-12	3	\N
2699	2630	missing	annual_physical	65	2026-10-12	3	\N
2700	2631	missing	annual_physical	65	2026-10-12	3	\N
2701	2632	missing	annual_physical	65	2026-10-12	3	\N
2702	2633	missing	annual_physical	65	2026-10-12	3	\N
2703	2634	missing	annual_physical	65	2026-10-12	3	\N
2704	2635	missing	annual_physical	65	2026-10-12	3	\N
2705	2636	missing	annual_physical	65	2026-10-12	3	\N
2706	2637	missing	annual_physical	65	2026-10-12	3	\N
2707	2638	missing	annual_physical	65	2026-10-12	3	\N
2708	2639	missing	annual_physical	65	2026-10-12	3	\N
2709	2640	missing	annual_physical	65	2026-10-12	3	\N
2710	2641	missing	annual_physical	65	2026-10-12	3	\N
2711	2642	missing	annual_physical	65	2026-10-12	3	\N
2712	2643	missing	annual_physical	65	2026-10-12	3	\N
2713	2644	missing	annual_physical	65	2026-10-12	3	\N
2714	2645	missing	annual_physical	65	2026-10-12	3	\N
2715	2646	missing	annual_physical	65	2026-10-12	3	\N
2716	2647	missing	annual_physical	65	2026-10-12	3	\N
2717	2648	missing	annual_physical	65	2026-10-12	3	\N
2718	2649	missing	annual_physical	65	2026-10-12	3	\N
2719	2650	missing	annual_physical	65	2026-10-12	3	\N
2720	2651	missing	annual_physical	65	2026-10-12	3	\N
2721	2652	missing	annual_physical	65	2026-10-12	3	\N
2722	2653	missing	annual_physical	65	2026-10-12	3	\N
2723	2654	missing	annual_physical	65	2026-10-12	3	\N
2724	2655	missing	annual_physical	65	2026-10-12	3	\N
2725	2656	missing	annual_physical	65	2026-10-12	3	\N
2726	2657	missing	annual_physical	65	2026-10-12	3	\N
2727	2658	missing	annual_physical	65	2026-10-12	3	\N
2728	2659	missing	annual_physical	65	2026-10-12	3	\N
2729	2660	missing	annual_physical	65	2026-10-12	3	\N
2730	2661	missing	annual_physical	65	2026-10-12	3	\N
2731	2662	missing	annual_physical	65	2026-10-12	3	\N
2732	2663	missing	annual_physical	65	2026-10-12	3	\N
2733	2664	missing	annual_physical	65	2026-10-12	3	\N
2734	2665	missing	annual_physical	65	2026-10-12	3	\N
2735	2666	missing	annual_physical	65	2026-10-12	3	\N
2736	2667	missing	annual_physical	65	2026-10-12	3	\N
2737	2668	missing	annual_physical	65	2026-10-12	3	\N
2738	2669	missing	annual_physical	65	2026-10-12	3	\N
2739	2670	missing	annual_physical	65	2026-10-12	3	\N
2740	2671	missing	annual_physical	65	2026-10-12	3	\N
2741	2672	missing	annual_physical	65	2026-10-12	3	\N
2742	2673	missing	annual_physical	65	2026-10-12	3	\N
2743	2674	missing	annual_physical	65	2026-10-12	3	\N
2744	2675	missing	annual_physical	65	2026-10-12	3	\N
2745	2676	missing	annual_physical	65	2026-10-12	3	\N
2746	2677	missing	annual_physical	65	2026-10-12	3	\N
2747	2678	missing	annual_physical	65	2026-10-12	3	\N
2748	2679	missing	annual_physical	65	2026-10-12	3	\N
2749	2680	missing	annual_physical	65	2026-10-12	3	\N
2750	2681	missing	annual_physical	65	2026-10-12	3	\N
2751	2682	missing	annual_physical	65	2026-10-12	3	\N
2752	2683	missing	annual_physical	65	2026-10-12	3	\N
2753	2684	missing	annual_physical	65	2026-10-12	3	\N
2754	2685	missing	annual_physical	65	2026-10-12	3	\N
2755	2686	missing	annual_physical	65	2026-10-12	3	\N
2756	2687	missing	annual_physical	65	2026-10-12	3	\N
2757	2688	missing	annual_physical	65	2026-10-12	3	\N
2758	2689	missing	annual_physical	65	2026-10-12	3	\N
2759	2690	missing	annual_physical	65	2026-10-12	3	\N
2760	2691	missing	annual_physical	65	2026-10-12	3	\N
2761	2692	missing	annual_physical	65	2026-10-12	3	\N
2762	2693	missing	annual_physical	65	2026-10-12	3	\N
2763	2694	missing	annual_physical	65	2026-10-12	3	\N
2764	2695	missing	annual_physical	65	2026-10-12	3	\N
2765	2696	missing	annual_physical	65	2026-10-12	3	\N
2766	2697	missing	annual_physical	65	2026-10-12	3	\N
2767	2698	missing	annual_physical	65	2026-10-12	3	\N
2768	2699	missing	annual_physical	65	2026-10-12	3	\N
2769	2700	missing	annual_physical	65	2026-10-12	3	\N
2770	2701	missing	annual_physical	65	2026-10-12	3	\N
2771	2702	missing	annual_physical	65	2026-10-12	3	\N
2772	2703	missing	annual_physical	65	2026-10-12	3	\N
2773	2704	missing	annual_physical	65	2026-10-12	3	\N
2774	2705	missing	annual_physical	65	2026-10-12	3	\N
2775	2706	missing	annual_physical	65	2026-10-12	3	\N
2776	2707	missing	annual_physical	65	2026-10-12	3	\N
2777	2708	missing	annual_physical	65	2026-10-12	3	\N
2778	2709	missing	annual_physical	65	2026-10-12	3	\N
2779	2710	missing	annual_physical	65	2026-10-12	3	\N
2780	2711	missing	annual_physical	65	2026-10-12	3	\N
2781	2712	missing	annual_physical	65	2026-10-12	3	\N
2782	2713	missing	annual_physical	65	2026-10-12	3	\N
2783	2714	missing	annual_physical	65	2026-10-12	3	\N
2784	2715	missing	annual_physical	65	2026-10-12	3	\N
2785	2716	missing	annual_physical	65	2026-10-12	3	\N
2786	2717	missing	annual_physical	65	2026-10-12	3	\N
2787	2718	missing	annual_physical	65	2026-10-12	3	\N
2788	2719	missing	annual_physical	65	2026-10-12	3	\N
2789	2720	missing	annual_physical	65	2026-10-12	3	\N
2790	2721	missing	annual_physical	65	2026-10-12	3	\N
2791	2722	missing	annual_physical	65	2026-10-12	3	\N
2792	2723	missing	annual_physical	65	2026-10-12	3	\N
2793	2724	missing	annual_physical	65	2026-10-12	3	\N
2794	2725	missing	annual_physical	65	2026-10-12	3	\N
2795	2726	missing	annual_physical	65	2026-10-12	3	\N
2796	2727	missing	annual_physical	65	2026-10-12	3	\N
2797	2728	missing	annual_physical	65	2026-10-12	3	\N
2798	2729	missing	annual_physical	65	2026-10-12	3	\N
2799	2730	missing	annual_physical	65	2026-10-12	3	\N
2800	2731	missing	annual_physical	65	2026-10-12	3	\N
2801	2732	missing	annual_physical	65	2026-10-12	3	\N
2802	2733	missing	annual_physical	65	2026-10-12	3	\N
2803	2734	missing	annual_physical	65	2026-10-12	3	\N
2804	2735	missing	annual_physical	65	2026-10-12	3	\N
2805	2736	missing	annual_physical	65	2026-10-12	3	\N
2806	2737	missing	annual_physical	65	2026-10-12	3	\N
2807	2738	missing	annual_physical	65	2026-10-12	3	\N
2808	2739	missing	annual_physical	65	2026-10-12	3	\N
2809	2740	missing	annual_physical	65	2026-10-12	3	\N
2810	2741	missing	annual_physical	65	2026-10-12	3	\N
2811	2742	missing	annual_physical	65	2026-10-12	3	\N
2812	2743	missing	annual_physical	65	2026-10-12	3	\N
2813	2744	missing	annual_physical	65	2026-10-12	3	\N
2814	2745	missing	annual_physical	65	2026-10-12	3	\N
2815	2746	missing	annual_physical	65	2026-10-12	3	\N
2816	2747	missing	annual_physical	65	2026-10-12	3	\N
2817	2748	missing	annual_physical	65	2026-10-12	3	\N
2818	2749	missing	annual_physical	65	2026-10-12	3	\N
2819	2750	missing	annual_physical	65	2026-10-12	3	\N
2820	2751	missing	annual_physical	65	2026-10-12	3	\N
2821	2752	missing	annual_physical	65	2026-10-12	3	\N
2822	2753	missing	annual_physical	65	2026-10-12	3	\N
2823	2754	missing	annual_physical	65	2026-10-12	3	\N
2824	2755	missing	annual_physical	65	2026-10-12	3	\N
2825	2756	missing	annual_physical	65	2026-10-12	3	\N
2826	2757	missing	annual_physical	65	2026-10-12	3	\N
2827	2758	missing	annual_physical	65	2026-10-12	3	\N
2828	2759	missing	annual_physical	65	2026-10-12	3	\N
2829	2760	missing	annual_physical	65	2026-10-12	3	\N
2830	2761	missing	annual_physical	65	2026-10-12	3	\N
2831	2762	missing	annual_physical	65	2026-10-12	3	\N
2832	2763	missing	annual_physical	65	2026-10-12	3	\N
2833	2764	missing	annual_physical	65	2026-10-12	3	\N
2834	2765	missing	annual_physical	65	2026-10-12	3	\N
2835	2766	missing	annual_physical	65	2026-10-12	3	\N
2836	2767	missing	annual_physical	65	2026-10-12	3	\N
2837	2768	missing	annual_physical	65	2026-10-12	3	\N
2838	2769	missing	annual_physical	65	2026-10-12	3	\N
2839	2770	missing	annual_physical	65	2026-10-12	3	\N
2840	2771	missing	annual_physical	65	2026-10-12	3	\N
2841	2772	missing	annual_physical	65	2026-10-12	3	\N
2842	2773	missing	annual_physical	65	2026-10-12	3	\N
2843	2774	missing	annual_physical	65	2026-10-12	3	\N
2844	2775	missing	annual_physical	65	2026-10-12	3	\N
2845	2776	missing	annual_physical	65	2026-10-12	3	\N
2846	2777	missing	annual_physical	65	2026-10-12	3	\N
2847	2778	missing	annual_physical	65	2026-10-12	3	\N
2848	2779	missing	annual_physical	65	2026-10-12	3	\N
2849	2780	missing	annual_physical	65	2026-10-12	3	\N
2850	2781	missing	annual_physical	65	2026-10-12	3	\N
2851	2782	missing	annual_physical	65	2026-10-12	3	\N
2852	2783	missing	annual_physical	65	2026-10-12	3	\N
2853	2784	missing	annual_physical	65	2026-10-12	3	\N
2854	2785	missing	annual_physical	65	2026-10-12	3	\N
2855	2786	missing	annual_physical	65	2026-10-12	3	\N
2856	2787	missing	annual_physical	65	2026-10-12	3	\N
2857	2788	missing	annual_physical	65	2026-10-12	3	\N
2858	2789	missing	annual_physical	65	2026-10-12	3	\N
2859	2790	missing	annual_physical	65	2026-10-12	3	\N
2860	2791	missing	annual_physical	65	2026-10-12	3	\N
2861	2792	missing	annual_physical	65	2026-10-12	3	\N
2862	2793	missing	annual_physical	65	2026-10-12	3	\N
2863	2794	missing	annual_physical	65	2026-10-12	3	\N
2864	2795	missing	annual_physical	65	2026-10-12	3	\N
2865	2796	missing	annual_physical	65	2026-10-12	3	\N
2866	2797	missing	annual_physical	65	2026-10-12	3	\N
2867	2798	missing	annual_physical	65	2026-10-12	3	\N
2868	2799	missing	annual_physical	65	2026-10-12	3	\N
2869	2800	missing	annual_physical	65	2026-10-12	3	\N
2870	2801	missing	annual_physical	65	2026-10-12	3	\N
2871	2802	missing	annual_physical	65	2026-10-12	3	\N
2872	2803	missing	annual_physical	65	2026-10-12	3	\N
2873	2804	missing	annual_physical	65	2026-10-12	3	\N
2874	2805	missing	annual_physical	65	2026-10-12	3	\N
2875	2806	missing	annual_physical	65	2026-10-12	3	\N
2876	2807	missing	annual_physical	65	2026-10-12	3	\N
2877	2808	missing	annual_physical	65	2026-10-12	3	\N
2878	2809	missing	annual_physical	65	2026-10-12	3	\N
2879	2810	missing	annual_physical	65	2026-10-12	3	\N
2880	2811	missing	annual_physical	65	2026-10-12	3	\N
2881	2812	missing	annual_physical	65	2026-10-12	3	\N
2882	2813	missing	annual_physical	65	2026-10-12	3	\N
2883	2814	missing	annual_physical	65	2026-10-12	3	\N
2884	2815	missing	annual_physical	65	2026-10-12	3	\N
2885	2816	missing	annual_physical	65	2026-10-12	3	\N
2886	2817	missing	annual_physical	65	2026-10-12	3	\N
2887	2818	missing	annual_physical	65	2026-10-12	3	\N
2888	2819	missing	annual_physical	65	2026-10-12	3	\N
2889	2820	missing	annual_physical	65	2026-10-12	3	\N
2890	2821	missing	annual_physical	65	2026-10-12	3	\N
2891	2822	missing	annual_physical	65	2026-10-12	3	\N
2892	2823	missing	annual_physical	65	2026-10-12	3	\N
2893	2824	missing	annual_physical	65	2026-10-12	3	\N
2894	2825	missing	annual_physical	65	2026-10-12	3	\N
2895	2826	missing	annual_physical	65	2026-10-12	3	\N
2896	2827	missing	annual_physical	65	2026-10-12	3	\N
2897	2828	missing	annual_physical	65	2026-10-12	3	\N
2898	2829	missing	annual_physical	65	2026-10-12	3	\N
2899	2830	missing	annual_physical	65	2026-10-12	3	\N
2900	2831	missing	annual_physical	65	2026-10-12	3	\N
2901	2832	missing	annual_physical	65	2026-10-12	3	\N
2902	2833	missing	annual_physical	65	2026-10-12	3	\N
2903	2834	missing	annual_physical	65	2026-10-12	3	\N
2904	2835	missing	annual_physical	65	2026-10-12	3	\N
2905	2836	missing	annual_physical	65	2026-10-12	3	\N
2906	2837	missing	annual_physical	65	2026-10-12	3	\N
2907	2838	missing	annual_physical	65	2026-10-12	3	\N
2908	2839	missing	annual_physical	65	2026-10-12	3	\N
2909	2840	missing	annual_physical	65	2026-10-12	3	\N
2910	2841	missing	annual_physical	65	2026-10-12	3	\N
2911	2842	missing	annual_physical	65	2026-10-12	3	\N
2912	2843	missing	annual_physical	65	2026-10-12	3	\N
2913	2844	missing	annual_physical	65	2026-10-12	3	\N
2914	2845	missing	annual_physical	65	2026-10-12	3	\N
2915	2846	missing	annual_physical	65	2026-10-12	3	\N
2916	2847	missing	annual_physical	65	2026-10-12	3	\N
2917	2848	missing	annual_physical	65	2026-10-12	3	\N
2918	2849	missing	annual_physical	65	2026-10-12	3	\N
2919	2850	missing	annual_physical	65	2026-10-12	3	\N
2920	2851	missing	annual_physical	65	2026-10-12	3	\N
2921	2852	missing	annual_physical	65	2026-10-12	3	\N
2922	2853	missing	annual_physical	65	2026-10-12	3	\N
2923	2854	missing	annual_physical	65	2026-10-12	3	\N
2924	2855	missing	annual_physical	65	2026-10-12	3	\N
2925	2856	missing	annual_physical	65	2026-10-12	3	\N
2926	2857	missing	annual_physical	65	2026-10-12	3	\N
2927	2858	missing	annual_physical	65	2026-10-12	3	\N
2928	2859	missing	annual_physical	65	2026-10-12	3	\N
2929	2860	missing	annual_physical	65	2026-10-12	3	\N
2930	2861	missing	annual_physical	65	2026-10-12	3	\N
2931	2862	missing	annual_physical	65	2026-10-12	3	\N
2932	2863	missing	annual_physical	65	2026-10-12	3	\N
2933	2864	missing	annual_physical	65	2026-10-12	3	\N
2934	2865	missing	annual_physical	65	2026-10-12	3	\N
2935	2866	missing	annual_physical	65	2026-10-12	3	\N
2936	2867	missing	annual_physical	65	2026-10-12	3	\N
2937	2868	missing	annual_physical	65	2026-10-12	3	\N
2938	2869	missing	annual_physical	65	2026-10-12	3	\N
2939	2870	missing	annual_physical	65	2026-10-12	3	\N
2940	2871	missing	annual_physical	65	2026-10-12	3	\N
2941	2872	missing	annual_physical	65	2026-10-12	3	\N
2942	2873	missing	annual_physical	65	2026-10-12	3	\N
2943	2874	missing	annual_physical	65	2026-10-12	3	\N
2944	2875	missing	annual_physical	65	2026-10-12	3	\N
2945	2876	missing	annual_physical	65	2026-10-12	3	\N
2946	2877	missing	annual_physical	65	2026-10-12	3	\N
2947	2878	missing	annual_physical	65	2026-10-12	3	\N
2948	2879	missing	annual_physical	65	2026-10-12	3	\N
2949	2880	missing	annual_physical	65	2026-10-12	3	\N
2950	2881	missing	annual_physical	65	2026-10-12	3	\N
2951	2882	missing	annual_physical	65	2026-10-12	3	\N
2952	2883	missing	annual_physical	65	2026-10-12	3	\N
2953	2884	missing	annual_physical	65	2026-10-12	3	\N
2954	2885	missing	annual_physical	65	2026-10-12	3	\N
2955	2886	missing	annual_physical	65	2026-10-12	3	\N
2956	2887	missing	annual_physical	65	2026-10-12	3	\N
2957	2888	missing	annual_physical	65	2026-10-12	3	\N
2958	2889	missing	annual_physical	65	2026-10-12	3	\N
2959	2890	missing	annual_physical	65	2026-10-12	3	\N
2960	2891	missing	annual_physical	65	2026-10-12	3	\N
2961	2892	missing	annual_physical	65	2026-10-12	3	\N
2962	2893	missing	annual_physical	65	2026-10-12	3	\N
2963	2894	missing	annual_physical	65	2026-10-12	3	\N
2964	2895	missing	annual_physical	65	2026-10-12	3	\N
2965	2896	missing	annual_physical	65	2026-10-12	3	\N
2966	2897	missing	annual_physical	65	2026-10-12	3	\N
2967	2898	missing	annual_physical	65	2026-10-12	3	\N
2968	2899	missing	annual_physical	65	2026-10-12	3	\N
2969	2900	missing	annual_physical	65	2026-10-12	3	\N
2970	2901	missing	annual_physical	65	2026-10-12	3	\N
2971	2902	missing	annual_physical	65	2026-10-12	3	\N
2972	2903	missing	annual_physical	65	2026-10-12	3	\N
2973	2904	missing	annual_physical	65	2026-10-12	3	\N
2974	2905	missing	annual_physical	65	2026-10-12	3	\N
2975	2906	missing	annual_physical	65	2026-10-12	3	\N
2976	2907	missing	annual_physical	65	2026-10-12	3	\N
2977	2908	missing	annual_physical	65	2026-10-12	3	\N
2978	2909	missing	annual_physical	65	2026-10-12	3	\N
2979	2910	missing	annual_physical	65	2026-10-12	3	\N
2980	2911	missing	annual_physical	65	2026-10-12	3	\N
2981	2912	missing	annual_physical	65	2026-10-12	3	\N
2982	2913	missing	annual_physical	65	2026-10-12	3	\N
2983	2914	missing	annual_physical	65	2026-10-12	3	\N
2984	2915	missing	annual_physical	65	2026-10-12	3	\N
2985	2916	missing	annual_physical	65	2026-10-12	3	\N
2986	2917	missing	annual_physical	65	2026-10-12	3	\N
2987	2918	missing	annual_physical	65	2026-10-12	3	\N
2988	2919	missing	annual_physical	65	2026-10-12	3	\N
2989	2920	missing	annual_physical	65	2026-10-12	3	\N
2990	2921	missing	annual_physical	65	2026-10-12	3	\N
2991	2922	missing	annual_physical	65	2026-10-12	3	\N
2992	2923	missing	annual_physical	65	2026-10-12	3	\N
2993	2924	missing	annual_physical	65	2026-10-12	3	\N
2994	2925	missing	annual_physical	65	2026-10-12	3	\N
2995	2926	missing	annual_physical	65	2026-10-12	3	\N
2996	2927	missing	annual_physical	65	2026-10-12	3	\N
2997	2928	missing	annual_physical	65	2026-10-12	3	\N
2998	2929	missing	annual_physical	65	2026-10-12	3	\N
2999	2930	missing	annual_physical	65	2026-10-12	3	\N
3000	2931	missing	annual_physical	65	2026-10-12	3	\N
3001	2932	missing	annual_physical	65	2026-10-12	3	\N
3002	2933	missing	annual_physical	65	2026-10-12	3	\N
3003	2934	missing	annual_physical	65	2026-10-12	3	\N
3004	2935	missing	annual_physical	65	2026-10-12	3	\N
3005	2936	missing	annual_physical	65	2026-10-12	3	\N
3006	2937	missing	annual_physical	65	2026-10-12	3	\N
3007	2938	missing	annual_physical	65	2026-10-12	3	\N
3008	2939	missing	annual_physical	65	2026-10-12	3	\N
3009	2940	missing	annual_physical	65	2026-10-12	3	\N
3010	2941	missing	annual_physical	65	2026-10-12	3	\N
3011	2942	missing	annual_physical	65	2026-10-12	3	\N
3012	2943	missing	annual_physical	65	2026-10-12	3	\N
3013	2944	missing	annual_physical	65	2026-10-12	3	\N
3014	2945	missing	annual_physical	65	2026-10-12	3	\N
3015	2946	missing	annual_physical	65	2026-10-12	3	\N
3016	2947	missing	annual_physical	65	2026-10-12	3	\N
3017	2948	missing	annual_physical	65	2026-10-12	3	\N
3018	2949	missing	annual_physical	65	2026-10-12	3	\N
3019	2950	missing	annual_physical	65	2026-10-12	3	\N
3020	2951	missing	annual_physical	65	2026-10-12	3	\N
3021	2952	missing	annual_physical	65	2026-10-12	3	\N
3022	2953	missing	annual_physical	65	2026-10-12	3	\N
3023	2954	missing	annual_physical	65	2026-10-12	3	\N
3024	2955	missing	annual_physical	65	2026-10-12	3	\N
3025	2956	missing	annual_physical	65	2026-10-12	3	\N
3026	2957	missing	annual_physical	65	2026-10-12	3	\N
3027	2958	missing	annual_physical	65	2026-10-12	3	\N
3028	2959	missing	annual_physical	65	2026-10-12	3	\N
3029	2960	missing	annual_physical	65	2026-10-12	3	\N
3030	2961	missing	annual_physical	65	2026-10-12	3	\N
3031	2962	missing	annual_physical	65	2026-10-12	3	\N
3032	2963	missing	annual_physical	65	2026-10-12	3	\N
3033	2964	missing	annual_physical	65	2026-10-12	3	\N
3034	2965	missing	annual_physical	65	2026-10-12	3	\N
3035	2966	missing	annual_physical	65	2026-10-12	3	\N
3036	2967	missing	annual_physical	65	2026-10-12	3	\N
3037	2968	missing	annual_physical	65	2026-10-12	3	\N
3038	2969	missing	annual_physical	65	2026-10-12	3	\N
3039	2970	missing	annual_physical	65	2026-10-12	3	\N
3040	2971	missing	annual_physical	65	2026-10-12	3	\N
3041	2972	missing	annual_physical	65	2026-10-12	3	\N
3042	2973	missing	annual_physical	65	2026-10-12	3	\N
3043	2974	missing	annual_physical	65	2026-10-12	3	\N
3044	2975	missing	annual_physical	65	2026-10-12	3	\N
3045	2976	missing	annual_physical	65	2026-10-12	3	\N
3046	2977	missing	annual_physical	65	2026-10-12	3	\N
3047	2978	missing	annual_physical	65	2026-10-12	3	\N
3048	2979	missing	annual_physical	65	2026-10-12	3	\N
3049	2980	missing	annual_physical	65	2026-10-12	3	\N
3050	2981	missing	annual_physical	65	2026-10-12	3	\N
3051	2982	missing	annual_physical	65	2026-10-12	3	\N
3052	2983	missing	annual_physical	65	2026-10-12	3	\N
3053	2984	missing	annual_physical	65	2026-10-12	3	\N
3054	2985	missing	annual_physical	65	2026-10-12	3	\N
3055	2986	missing	annual_physical	65	2026-10-12	3	\N
3056	2987	missing	annual_physical	65	2026-10-12	3	\N
3057	2988	missing	annual_physical	65	2026-10-12	3	\N
3058	2989	missing	annual_physical	65	2026-10-12	3	\N
3059	2990	missing	annual_physical	65	2026-10-12	3	\N
3060	2991	missing	annual_physical	65	2026-10-12	3	\N
3061	2992	missing	annual_physical	65	2026-10-12	3	\N
3062	2993	missing	annual_physical	65	2026-10-12	3	\N
3063	2994	missing	annual_physical	65	2026-10-12	3	\N
3064	2995	missing	annual_physical	65	2026-10-12	3	\N
3065	2996	missing	annual_physical	65	2026-10-12	3	\N
3066	2997	missing	annual_physical	65	2026-10-12	3	\N
3067	2998	missing	annual_physical	65	2026-10-12	3	\N
3068	2999	missing	annual_physical	65	2026-10-12	3	\N
3069	3000	missing	annual_physical	65	2026-10-12	3	\N
3070	3001	missing	annual_physical	65	2026-10-12	3	\N
3071	3002	missing	annual_physical	65	2026-10-12	3	\N
3072	3003	missing	annual_physical	65	2026-10-12	3	\N
3073	3004	missing	annual_physical	65	2026-10-12	3	\N
3074	3005	missing	annual_physical	65	2026-10-12	3	\N
3075	3006	missing	annual_physical	65	2026-10-12	3	\N
3076	3007	missing	annual_physical	65	2026-10-12	3	\N
3077	3008	missing	annual_physical	65	2026-10-12	3	\N
3078	3009	missing	annual_physical	65	2026-10-12	3	\N
3079	3010	missing	annual_physical	65	2026-10-12	3	\N
3080	3011	missing	annual_physical	65	2026-10-12	3	\N
3081	3012	missing	annual_physical	65	2026-10-12	3	\N
3082	3013	missing	annual_physical	65	2026-10-12	3	\N
3083	3014	missing	annual_physical	65	2026-10-12	3	\N
3084	3015	missing	annual_physical	65	2026-10-12	3	\N
3085	3016	missing	annual_physical	65	2026-10-12	3	\N
3086	3017	missing	annual_physical	65	2026-10-12	3	\N
3087	3018	missing	annual_physical	65	2026-10-12	3	\N
3088	3019	missing	annual_physical	65	2026-10-12	3	\N
3089	3020	missing	annual_physical	65	2026-10-12	3	\N
3090	3021	missing	annual_physical	65	2026-10-12	3	\N
3091	3022	missing	annual_physical	65	2026-10-12	3	\N
3092	3023	missing	annual_physical	65	2026-10-12	3	\N
3093	3024	missing	annual_physical	65	2026-10-12	3	\N
3094	3025	missing	annual_physical	65	2026-10-12	3	\N
3095	3026	missing	annual_physical	65	2026-10-12	3	\N
3096	3027	missing	annual_physical	65	2026-10-12	3	\N
3097	3028	missing	annual_physical	65	2026-10-12	3	\N
3098	3029	missing	annual_physical	65	2026-10-12	3	\N
3099	3030	missing	annual_physical	65	2026-10-12	3	\N
3100	3031	missing	annual_physical	65	2026-10-12	3	\N
3101	3032	missing	annual_physical	65	2026-10-12	3	\N
3102	3033	missing	annual_physical	65	2026-10-12	3	\N
3103	3034	missing	annual_physical	65	2026-10-12	3	\N
3104	3035	missing	annual_physical	65	2026-10-12	3	\N
3105	3036	missing	annual_physical	65	2026-10-12	3	\N
3106	3037	missing	annual_physical	65	2026-10-12	3	\N
3107	3038	missing	annual_physical	65	2026-10-12	3	\N
3108	3039	missing	annual_physical	65	2026-10-12	3	\N
3109	3040	missing	annual_physical	65	2026-10-12	3	\N
3110	3041	missing	annual_physical	65	2026-10-12	3	\N
3111	3042	missing	annual_physical	65	2026-10-12	3	\N
3112	3043	missing	annual_physical	65	2026-10-12	3	\N
3113	3044	missing	annual_physical	65	2026-10-12	3	\N
3114	3045	missing	annual_physical	65	2026-10-12	3	\N
3115	3046	missing	annual_physical	65	2026-10-12	3	\N
3116	3047	missing	annual_physical	65	2026-10-12	3	\N
3117	3048	missing	annual_physical	65	2026-10-12	3	\N
3118	3049	missing	annual_physical	65	2026-10-12	3	\N
3119	3050	missing	annual_physical	65	2026-10-12	3	\N
3120	3051	missing	annual_physical	65	2026-10-12	3	\N
3121	3052	missing	annual_physical	65	2026-10-12	3	\N
3122	3053	missing	annual_physical	65	2026-10-12	3	\N
3123	3054	missing	annual_physical	65	2026-10-12	3	\N
3124	3055	missing	annual_physical	65	2026-10-12	3	\N
3125	3056	missing	annual_physical	65	2026-10-12	3	\N
3126	3057	missing	annual_physical	65	2026-10-12	3	\N
3127	3058	missing	annual_physical	65	2026-10-12	3	\N
3128	3059	missing	annual_physical	65	2026-10-12	3	\N
3129	3060	missing	annual_physical	65	2026-10-12	3	\N
3130	3061	missing	annual_physical	65	2026-10-12	3	\N
3131	3062	missing	annual_physical	65	2026-10-12	3	\N
3132	3063	missing	annual_physical	65	2026-10-12	3	\N
3133	3064	missing	annual_physical	65	2026-10-12	3	\N
3134	3065	missing	annual_physical	65	2026-10-12	3	\N
3135	3066	missing	annual_physical	65	2026-10-12	3	\N
3136	3067	missing	annual_physical	65	2026-10-12	3	\N
3137	3068	missing	annual_physical	65	2026-10-12	3	\N
3138	3069	missing	annual_physical	65	2026-10-12	3	\N
3139	3070	missing	annual_physical	65	2026-10-12	3	\N
3140	3071	missing	annual_physical	65	2026-10-12	3	\N
3141	3072	missing	annual_physical	65	2026-10-12	3	\N
3142	3073	missing	annual_physical	65	2026-10-12	3	\N
3143	3074	missing	annual_physical	65	2026-10-12	3	\N
3144	3075	missing	annual_physical	65	2026-10-12	3	\N
3145	3076	missing	annual_physical	65	2026-10-12	3	\N
3146	3077	missing	annual_physical	65	2026-10-12	3	\N
3147	3078	missing	annual_physical	65	2026-10-12	3	\N
3148	3079	missing	annual_physical	65	2026-10-12	3	\N
3149	3080	missing	annual_physical	65	2026-10-12	3	\N
3150	3081	missing	annual_physical	65	2026-10-12	3	\N
3151	3082	missing	annual_physical	65	2026-10-12	3	\N
3152	3083	missing	annual_physical	65	2026-10-12	3	\N
3153	3084	missing	annual_physical	65	2026-10-12	3	\N
3154	3085	missing	annual_physical	65	2026-10-12	3	\N
3155	3086	missing	annual_physical	65	2026-10-12	3	\N
3156	3087	missing	annual_physical	65	2026-10-12	3	\N
3157	3088	missing	annual_physical	65	2026-10-12	3	\N
3158	3089	missing	annual_physical	65	2026-10-12	3	\N
3159	3090	missing	annual_physical	65	2026-10-12	3	\N
3160	3091	missing	annual_physical	65	2026-10-12	3	\N
3161	3092	missing	annual_physical	65	2026-10-12	3	\N
3162	3093	missing	annual_physical	65	2026-10-12	3	\N
3163	3094	missing	annual_physical	65	2026-10-12	3	\N
3164	3095	missing	annual_physical	65	2026-10-12	3	\N
3165	3096	missing	annual_physical	65	2026-10-12	3	\N
3166	3097	missing	annual_physical	65	2026-10-12	3	\N
3167	3098	missing	annual_physical	65	2026-10-12	3	\N
3168	3099	missing	annual_physical	65	2026-10-12	3	\N
3169	3100	missing	annual_physical	65	2026-10-12	3	\N
3170	3101	missing	annual_physical	65	2026-10-12	3	\N
3171	3102	missing	annual_physical	65	2026-10-12	3	\N
3172	3103	missing	annual_physical	65	2026-10-12	3	\N
3173	3104	missing	annual_physical	65	2026-10-12	3	\N
3174	3105	missing	annual_physical	65	2026-10-12	3	\N
3175	3106	missing	annual_physical	65	2026-10-12	3	\N
3176	3107	missing	annual_physical	65	2026-10-12	3	\N
3177	3108	missing	annual_physical	65	2026-10-12	3	\N
3178	3109	missing	annual_physical	65	2026-10-12	3	\N
3179	3110	missing	annual_physical	65	2026-10-12	3	\N
3180	3111	missing	annual_physical	65	2026-10-12	3	\N
3181	3112	missing	annual_physical	65	2026-10-12	3	\N
3182	3113	missing	annual_physical	65	2026-10-12	3	\N
3183	3114	missing	annual_physical	65	2026-10-12	3	\N
3184	3115	missing	annual_physical	65	2026-10-12	3	\N
3185	3116	missing	annual_physical	65	2026-10-12	3	\N
3186	3117	missing	annual_physical	65	2026-10-12	3	\N
3187	3118	missing	annual_physical	65	2026-10-12	3	\N
3188	3119	missing	annual_physical	65	2026-10-12	3	\N
3189	3120	missing	annual_physical	65	2026-10-12	3	\N
3190	3121	missing	annual_physical	65	2026-10-12	3	\N
3191	3122	missing	annual_physical	65	2026-10-12	3	\N
3192	3123	missing	annual_physical	65	2026-10-12	3	\N
3193	3124	missing	annual_physical	65	2026-10-12	3	\N
3194	3125	missing	annual_physical	65	2026-10-12	3	\N
3195	3126	missing	annual_physical	65	2026-10-12	3	\N
3196	3127	missing	annual_physical	65	2026-10-12	3	\N
3197	3128	missing	annual_physical	65	2026-10-12	3	\N
3198	3129	missing	annual_physical	65	2026-10-12	3	\N
3199	3130	missing	annual_physical	65	2026-10-12	3	\N
3200	3131	missing	annual_physical	65	2026-10-12	3	\N
3201	3132	missing	annual_physical	65	2026-10-12	3	\N
3202	3133	missing	annual_physical	65	2026-10-12	3	\N
3203	3134	missing	annual_physical	65	2026-10-12	3	\N
3204	3135	missing	annual_physical	65	2026-10-12	3	\N
3205	3136	missing	annual_physical	65	2026-10-12	3	\N
3206	3137	missing	annual_physical	65	2026-10-12	3	\N
3207	3138	missing	annual_physical	65	2026-10-12	3	\N
3208	3139	missing	annual_physical	65	2026-10-12	3	\N
3209	3140	missing	annual_physical	65	2026-10-12	3	\N
3210	3141	missing	annual_physical	65	2026-10-12	3	\N
3211	3142	missing	annual_physical	65	2026-10-12	3	\N
3212	3143	missing	annual_physical	65	2026-10-12	3	\N
3213	3144	missing	annual_physical	65	2026-10-12	3	\N
3214	3145	missing	annual_physical	65	2026-10-12	3	\N
3215	3146	missing	annual_physical	65	2026-10-12	3	\N
3216	3147	missing	annual_physical	65	2026-10-12	3	\N
3217	3148	missing	annual_physical	65	2026-10-12	3	\N
3218	3149	missing	annual_physical	65	2026-10-12	3	\N
3219	3150	missing	annual_physical	65	2026-10-12	3	\N
3220	3151	missing	annual_physical	65	2026-10-12	3	\N
3221	3152	missing	annual_physical	65	2026-10-12	3	\N
3222	3153	missing	annual_physical	65	2026-10-12	3	\N
3223	3154	missing	annual_physical	65	2026-10-12	3	\N
3224	3155	missing	annual_physical	65	2026-10-12	3	\N
3225	3156	missing	annual_physical	65	2026-10-12	3	\N
3226	3157	missing	annual_physical	65	2026-10-12	3	\N
3227	3158	missing	annual_physical	65	2026-10-12	3	\N
3228	3159	missing	annual_physical	65	2026-10-12	3	\N
3229	3160	missing	annual_physical	65	2026-10-12	3	\N
3230	3161	missing	annual_physical	65	2026-10-12	3	\N
3231	3162	missing	annual_physical	65	2026-10-12	3	\N
3232	3163	missing	annual_physical	65	2026-10-12	3	\N
3233	3164	missing	annual_physical	65	2026-10-12	3	\N
3234	3165	missing	annual_physical	65	2026-10-12	3	\N
3235	3166	missing	annual_physical	65	2026-10-12	3	\N
3236	3167	missing	annual_physical	65	2026-10-12	3	\N
3237	3168	missing	annual_physical	65	2026-10-12	3	\N
3238	3169	missing	annual_physical	65	2026-10-12	3	\N
3239	3170	missing	annual_physical	65	2026-10-12	3	\N
3240	3171	missing	annual_physical	65	2026-10-12	3	\N
3241	3172	missing	annual_physical	65	2026-10-12	3	\N
3242	3173	missing	annual_physical	65	2026-10-12	3	\N
3243	3174	missing	annual_physical	65	2026-10-12	3	\N
3244	3175	missing	annual_physical	65	2026-10-12	3	\N
3245	3176	borrowed	annual_physical	65	2026-10-12	3	\N
3246	3177	missing	annual_physical	65	2026-10-12	3	\N
3247	3178	missing	annual_physical	65	2026-10-12	3	\N
3248	3179	missing	annual_physical	65	2026-10-12	3	\N
3249	3180	missing	annual_physical	65	2026-10-12	3	\N
3250	3181	missing	annual_physical	65	2026-10-12	3	\N
3251	3182	missing	annual_physical	65	2026-10-12	3	\N
3252	3183	missing	annual_physical	65	2026-10-12	3	\N
3253	3184	missing	annual_physical	65	2026-10-12	3	\N
3254	3185	missing	annual_physical	65	2026-10-12	3	\N
3255	3186	missing	annual_physical	65	2026-10-12	3	\N
3256	3187	missing	annual_physical	65	2026-10-12	3	\N
3257	3188	missing	annual_physical	65	2026-10-12	3	\N
3258	3189	missing	annual_physical	65	2026-10-12	3	\N
3259	3190	missing	annual_physical	65	2026-10-12	3	\N
3260	3191	missing	annual_physical	65	2026-10-12	3	\N
3261	3192	missing	annual_physical	65	2026-10-12	3	\N
3262	3193	missing	annual_physical	65	2026-10-12	3	\N
3263	3194	missing	annual_physical	65	2026-10-12	3	\N
3264	3195	missing	annual_physical	65	2026-10-12	3	\N
3265	3196	missing	annual_physical	65	2026-10-12	3	\N
3266	3197	missing	annual_physical	65	2026-10-12	3	\N
3267	3198	missing	annual_physical	65	2026-10-12	3	\N
3268	3199	missing	annual_physical	65	2026-10-12	3	\N
3269	3200	missing	annual_physical	65	2026-10-12	3	\N
3270	3201	missing	annual_physical	65	2026-10-12	3	\N
3271	3202	missing	annual_physical	65	2026-10-12	3	\N
3272	3203	missing	annual_physical	65	2026-10-12	3	\N
3273	3204	missing	annual_physical	65	2026-10-12	3	\N
3274	3205	missing	annual_physical	65	2026-10-12	3	\N
3275	3206	missing	annual_physical	65	2026-10-12	3	\N
3276	3207	missing	annual_physical	65	2026-10-12	3	\N
3277	3208	missing	annual_physical	65	2026-10-12	3	\N
3278	3209	missing	annual_physical	65	2026-10-12	3	\N
3279	3210	missing	annual_physical	65	2026-10-12	3	\N
3280	3211	missing	annual_physical	65	2026-10-12	3	\N
3281	3212	missing	annual_physical	65	2026-10-12	3	\N
3282	3213	missing	annual_physical	65	2026-10-12	3	\N
3283	3214	missing	annual_physical	65	2026-10-12	3	\N
3284	3215	missing	annual_physical	65	2026-10-12	3	\N
3285	3216	missing	annual_physical	65	2026-10-12	3	\N
3286	3217	missing	annual_physical	65	2026-10-12	3	\N
3287	3218	missing	annual_physical	65	2026-10-12	3	\N
3288	3219	missing	annual_physical	65	2026-10-12	3	\N
3289	3220	missing	annual_physical	65	2026-10-12	3	\N
3290	3221	missing	annual_physical	65	2026-10-12	3	\N
3291	3222	missing	annual_physical	65	2026-10-12	3	\N
3292	3223	missing	annual_physical	65	2026-10-12	3	\N
3293	3224	missing	annual_physical	65	2026-10-12	3	\N
3294	3225	missing	annual_physical	65	2026-10-12	3	\N
3295	3226	missing	annual_physical	65	2026-10-12	3	\N
3296	3227	missing	annual_physical	65	2026-10-12	3	\N
3297	3228	missing	annual_physical	65	2026-10-12	3	\N
3298	3229	missing	annual_physical	65	2026-10-12	3	\N
3299	3230	missing	annual_physical	65	2026-10-12	3	\N
3300	3231	missing	annual_physical	65	2026-10-12	3	\N
3301	3232	missing	annual_physical	65	2026-10-12	3	\N
3302	3233	missing	annual_physical	65	2026-10-12	3	\N
3303	3234	missing	annual_physical	65	2026-10-12	3	\N
3304	3235	missing	annual_physical	65	2026-10-12	3	\N
3305	3236	missing	annual_physical	65	2026-10-12	3	\N
3306	3237	missing	annual_physical	65	2026-10-12	3	\N
3307	3238	missing	annual_physical	65	2026-10-12	3	\N
3308	3239	missing	annual_physical	65	2026-10-12	3	\N
3309	3240	missing	annual_physical	65	2026-10-12	3	\N
3310	3241	missing	annual_physical	65	2026-10-12	3	\N
3311	3242	missing	annual_physical	65	2026-10-12	3	\N
3312	3243	missing	annual_physical	65	2026-10-12	3	\N
3313	3244	missing	annual_physical	65	2026-10-12	3	\N
3314	3245	missing	annual_physical	65	2026-10-12	3	\N
3315	3246	missing	annual_physical	65	2026-10-12	3	\N
3316	3247	missing	annual_physical	65	2026-10-12	3	\N
3317	3248	missing	annual_physical	65	2026-10-12	3	\N
3318	3249	missing	annual_physical	65	2026-10-12	3	\N
3319	3250	missing	annual_physical	65	2026-10-12	3	\N
3320	3251	missing	annual_physical	65	2026-10-12	3	\N
3321	3252	missing	annual_physical	65	2026-10-12	3	\N
3322	3253	missing	annual_physical	65	2026-10-12	3	\N
3323	3254	missing	annual_physical	65	2026-10-12	3	\N
3324	3255	missing	annual_physical	65	2026-10-12	3	\N
3325	3256	missing	annual_physical	65	2026-10-12	3	\N
3326	3257	missing	annual_physical	65	2026-10-12	3	\N
3327	3258	missing	annual_physical	65	2026-10-12	3	\N
3328	3259	missing	annual_physical	65	2026-10-12	3	\N
3329	3260	missing	annual_physical	65	2026-10-12	3	\N
3330	3261	missing	annual_physical	65	2026-10-12	3	\N
3331	3262	missing	annual_physical	65	2026-10-12	3	\N
3332	3263	missing	annual_physical	65	2026-10-12	3	\N
3333	3264	missing	annual_physical	65	2026-10-12	3	\N
3334	3265	missing	annual_physical	65	2026-10-12	3	\N
3335	3266	missing	annual_physical	65	2026-10-12	3	\N
3336	3267	missing	annual_physical	65	2026-10-12	3	\N
3337	3268	missing	annual_physical	65	2026-10-12	3	\N
3338	3269	missing	annual_physical	65	2026-10-12	3	\N
3339	3270	missing	annual_physical	65	2026-10-12	3	\N
3340	3271	missing	annual_physical	65	2026-10-12	3	\N
3341	3272	missing	annual_physical	65	2026-10-12	3	\N
3342	3273	missing	annual_physical	65	2026-10-12	3	\N
3343	3274	missing	annual_physical	65	2026-10-12	3	\N
3344	3275	missing	annual_physical	65	2026-10-12	3	\N
3345	3276	missing	annual_physical	65	2026-10-12	3	\N
3346	3277	missing	annual_physical	65	2026-10-12	3	\N
3347	3278	missing	annual_physical	65	2026-10-12	3	\N
3348	3279	missing	annual_physical	65	2026-10-12	3	\N
3349	3280	missing	annual_physical	65	2026-10-12	3	\N
3350	3281	missing	annual_physical	65	2026-10-12	3	\N
3351	3282	missing	annual_physical	65	2026-10-12	3	\N
3352	3283	missing	annual_physical	65	2026-10-12	3	\N
3353	3284	missing	annual_physical	65	2026-10-12	3	\N
3354	3285	missing	annual_physical	65	2026-10-12	3	\N
3355	3286	missing	annual_physical	65	2026-10-12	3	\N
3356	3287	missing	annual_physical	65	2026-10-12	3	\N
3357	3288	missing	annual_physical	65	2026-10-12	3	\N
3358	3289	missing	annual_physical	65	2026-10-12	3	\N
3359	3290	missing	annual_physical	65	2026-10-12	3	\N
3360	3291	missing	annual_physical	65	2026-10-12	3	\N
3361	3292	missing	annual_physical	65	2026-10-12	3	\N
3362	3293	missing	annual_physical	65	2026-10-12	3	\N
3363	3294	missing	annual_physical	65	2026-10-12	3	\N
3364	3295	missing	annual_physical	65	2026-10-12	3	\N
3365	3296	missing	annual_physical	65	2026-10-12	3	\N
3366	3297	missing	annual_physical	65	2026-10-12	3	\N
3367	3298	missing	annual_physical	65	2026-10-12	3	\N
3368	3299	missing	annual_physical	65	2026-10-12	3	\N
3369	3300	missing	annual_physical	65	2026-10-12	3	\N
3370	3301	missing	annual_physical	65	2026-10-12	3	\N
3371	3302	missing	annual_physical	65	2026-10-12	3	\N
3372	3303	missing	annual_physical	65	2026-10-12	3	\N
3373	3304	missing	annual_physical	65	2026-10-12	3	\N
3374	3305	missing	annual_physical	65	2026-10-12	3	\N
3375	3306	missing	annual_physical	65	2026-10-12	3	\N
3376	3307	missing	annual_physical	65	2026-10-12	3	\N
3377	3308	missing	annual_physical	65	2026-10-12	3	\N
3378	3309	missing	annual_physical	65	2026-10-12	3	\N
3379	3310	missing	annual_physical	65	2026-10-12	3	\N
3380	3311	missing	annual_physical	65	2026-10-12	3	\N
3381	3312	missing	annual_physical	65	2026-10-12	3	\N
3382	3313	missing	annual_physical	65	2026-10-12	3	\N
3383	3314	missing	annual_physical	65	2026-10-12	3	\N
3384	3315	missing	annual_physical	65	2026-10-12	3	\N
3385	3316	missing	annual_physical	65	2026-10-12	3	\N
3386	3317	missing	annual_physical	65	2026-10-12	3	\N
3387	3318	missing	annual_physical	65	2026-10-12	3	\N
3388	3319	missing	annual_physical	65	2026-10-12	3	\N
3389	3320	missing	annual_physical	65	2026-10-12	3	\N
3390	3321	missing	annual_physical	65	2026-10-12	3	\N
3391	3322	missing	annual_physical	65	2026-10-12	3	\N
3392	3323	missing	annual_physical	65	2026-10-12	3	\N
3393	3324	missing	annual_physical	65	2026-10-12	3	\N
3394	3325	missing	annual_physical	65	2026-10-12	3	\N
3395	3326	missing	annual_physical	65	2026-10-12	3	\N
3396	3327	missing	annual_physical	65	2026-10-12	3	\N
3397	3328	missing	annual_physical	65	2026-10-12	3	\N
3398	3329	missing	annual_physical	65	2026-10-12	3	\N
3399	3330	missing	annual_physical	65	2026-10-12	3	\N
3400	3331	missing	annual_physical	65	2026-10-12	3	\N
3401	3332	missing	annual_physical	65	2026-10-12	3	\N
3402	3333	missing	annual_physical	65	2026-10-12	3	\N
3403	3334	missing	annual_physical	65	2026-10-12	3	\N
3404	3335	missing	annual_physical	65	2026-10-12	3	\N
3405	3336	missing	annual_physical	65	2026-10-12	3	\N
3406	3337	missing	annual_physical	65	2026-10-12	3	\N
3407	3338	missing	annual_physical	65	2026-10-12	3	\N
3408	3339	missing	annual_physical	65	2026-10-12	3	\N
3409	3340	missing	annual_physical	65	2026-10-12	3	\N
3410	3341	missing	annual_physical	65	2026-10-12	3	\N
3411	3342	missing	annual_physical	65	2026-10-12	3	\N
3412	3343	missing	annual_physical	65	2026-10-12	3	\N
3413	3344	missing	annual_physical	65	2026-10-12	3	\N
3414	3345	missing	annual_physical	65	2026-10-12	3	\N
3415	3346	missing	annual_physical	65	2026-10-12	3	\N
3416	3347	missing	annual_physical	65	2026-10-12	3	\N
3417	3348	missing	annual_physical	65	2026-10-12	3	\N
3418	3349	missing	annual_physical	65	2026-10-12	3	\N
3419	3350	missing	annual_physical	65	2026-10-12	3	\N
3420	3351	missing	annual_physical	65	2026-10-12	3	\N
3421	3352	missing	annual_physical	65	2026-10-12	3	\N
3422	3353	missing	annual_physical	65	2026-10-12	3	\N
3423	3354	missing	annual_physical	65	2026-10-12	3	\N
3424	3355	missing	annual_physical	65	2026-10-12	3	\N
3425	3356	missing	annual_physical	65	2026-10-12	3	\N
3426	3357	missing	annual_physical	65	2026-10-12	3	\N
3427	3358	missing	annual_physical	65	2026-10-12	3	\N
3428	3359	missing	annual_physical	65	2026-10-12	3	\N
3429	3360	missing	annual_physical	65	2026-10-12	3	\N
3430	3361	missing	annual_physical	65	2026-10-12	3	\N
3431	3362	missing	annual_physical	65	2026-10-12	3	\N
3432	3363	missing	annual_physical	65	2026-10-12	3	\N
3433	3364	missing	annual_physical	65	2026-10-12	3	\N
3434	3365	missing	annual_physical	65	2026-10-12	3	\N
3435	3366	missing	annual_physical	65	2026-10-12	3	\N
3436	3367	missing	annual_physical	65	2026-10-12	3	\N
3437	3368	missing	annual_physical	65	2026-10-12	3	\N
3438	3369	missing	annual_physical	65	2026-10-12	3	\N
3439	3370	missing	annual_physical	65	2026-10-12	3	\N
3440	3371	missing	annual_physical	65	2026-10-12	3	\N
3441	3372	missing	annual_physical	65	2026-10-12	3	\N
3442	3373	missing	annual_physical	65	2026-10-12	3	\N
3443	3374	missing	annual_physical	65	2026-10-12	3	\N
3444	3375	missing	annual_physical	65	2026-10-12	3	\N
3445	3376	missing	annual_physical	65	2026-10-12	3	\N
3446	3377	missing	annual_physical	65	2026-10-12	3	\N
3447	3378	missing	annual_physical	65	2026-10-12	3	\N
3448	3379	missing	annual_physical	65	2026-10-12	3	\N
3449	3380	missing	annual_physical	65	2026-10-12	3	\N
3450	3381	missing	annual_physical	65	2026-10-12	3	\N
3451	3382	missing	annual_physical	65	2026-10-12	3	\N
3452	3383	missing	annual_physical	65	2026-10-12	3	\N
3453	3384	missing	annual_physical	65	2026-10-12	3	\N
3454	3385	missing	annual_physical	65	2026-10-12	3	\N
3455	3386	missing	annual_physical	65	2026-10-12	3	\N
3456	3387	missing	annual_physical	65	2026-10-12	3	\N
3457	3388	missing	annual_physical	65	2026-10-12	3	\N
3458	3389	missing	annual_physical	65	2026-10-12	3	\N
3459	3390	missing	annual_physical	65	2026-10-12	3	\N
3460	3391	missing	annual_physical	65	2026-10-12	3	\N
3461	3392	missing	annual_physical	65	2026-10-12	3	\N
3462	3393	missing	annual_physical	65	2026-10-12	3	\N
3463	3394	missing	annual_physical	65	2026-10-12	3	\N
3464	3395	missing	annual_physical	65	2026-10-12	3	\N
3465	3396	missing	annual_physical	65	2026-10-12	3	\N
3466	3397	missing	annual_physical	65	2026-10-12	3	\N
3467	3398	missing	annual_physical	65	2026-10-12	3	\N
3468	3399	missing	annual_physical	65	2026-10-12	3	\N
3469	3400	missing	annual_physical	65	2026-10-12	3	\N
3470	3401	missing	annual_physical	65	2026-10-12	3	\N
3471	3402	missing	annual_physical	65	2026-10-12	3	\N
3472	3403	missing	annual_physical	65	2026-10-12	3	\N
3473	3404	missing	annual_physical	65	2026-10-12	3	\N
3474	3405	missing	annual_physical	65	2026-10-12	3	\N
3475	3406	missing	annual_physical	65	2026-10-12	3	\N
3476	3407	missing	annual_physical	65	2026-10-12	3	\N
3477	3408	missing	annual_physical	65	2026-10-12	3	\N
3478	3409	missing	annual_physical	65	2026-10-12	3	\N
3479	3410	missing	annual_physical	65	2026-10-12	3	\N
3480	3411	missing	annual_physical	65	2026-10-12	3	\N
3481	3412	missing	annual_physical	65	2026-10-12	3	\N
3482	3413	missing	annual_physical	65	2026-10-12	3	\N
3483	3414	missing	annual_physical	65	2026-10-12	3	\N
3484	3415	missing	annual_physical	65	2026-10-12	3	\N
3485	3416	missing	annual_physical	65	2026-10-12	3	\N
3486	3417	missing	annual_physical	65	2026-10-12	3	\N
3487	3418	missing	annual_physical	65	2026-10-12	3	\N
3488	3419	missing	annual_physical	65	2026-10-12	3	\N
3489	3420	missing	annual_physical	65	2026-10-12	3	\N
3490	3421	missing	annual_physical	65	2026-10-12	3	\N
3491	3422	missing	annual_physical	65	2026-10-12	3	\N
3492	3423	missing	annual_physical	65	2026-10-12	3	\N
3493	3424	missing	annual_physical	65	2026-10-12	3	\N
3494	3425	missing	annual_physical	65	2026-10-12	3	\N
3495	3426	missing	annual_physical	65	2026-10-12	3	\N
3496	3427	missing	annual_physical	65	2026-10-12	3	\N
3497	3428	missing	annual_physical	65	2026-10-12	3	\N
3498	3429	missing	annual_physical	65	2026-10-12	3	\N
3499	3430	missing	annual_physical	65	2026-10-12	3	\N
3500	3431	missing	annual_physical	65	2026-10-12	3	\N
3501	3432	missing	annual_physical	65	2026-10-12	3	\N
3502	3433	missing	annual_physical	65	2026-10-12	3	\N
3503	3434	missing	annual_physical	65	2026-10-12	3	\N
3504	3435	missing	annual_physical	65	2026-10-12	3	\N
3505	3436	missing	annual_physical	65	2026-10-12	3	\N
3506	3437	missing	annual_physical	65	2026-10-12	3	\N
3507	3438	missing	annual_physical	65	2026-10-12	3	\N
3508	3439	missing	annual_physical	65	2026-10-12	3	\N
3509	3440	missing	annual_physical	65	2026-10-12	3	\N
3510	3441	missing	annual_physical	65	2026-10-12	3	\N
3511	3442	missing	annual_physical	65	2026-10-12	3	\N
3512	3443	missing	annual_physical	65	2026-10-12	3	\N
3513	3444	missing	annual_physical	65	2026-10-12	3	\N
3514	3445	missing	annual_physical	65	2026-10-12	3	\N
3515	3446	missing	annual_physical	65	2026-10-12	3	\N
3516	3447	missing	annual_physical	65	2026-10-12	3	\N
3517	3448	missing	annual_physical	65	2026-10-12	3	\N
3518	3449	missing	annual_physical	65	2026-10-12	3	\N
3519	3450	missing	annual_physical	65	2026-10-12	3	\N
3520	3451	missing	annual_physical	65	2026-10-12	3	\N
3521	3452	missing	annual_physical	65	2026-10-12	3	\N
3522	3453	missing	annual_physical	65	2026-10-12	3	\N
3523	3454	missing	annual_physical	65	2026-10-12	3	\N
3524	3455	missing	annual_physical	65	2026-10-12	3	\N
3525	3456	missing	annual_physical	65	2026-10-12	3	\N
3526	3457	missing	annual_physical	65	2026-10-12	3	\N
3527	3458	missing	annual_physical	65	2026-10-12	3	\N
3528	3459	missing	annual_physical	65	2026-10-12	3	\N
3529	3460	missing	annual_physical	65	2026-10-12	3	\N
3530	3461	missing	annual_physical	65	2026-10-12	3	\N
3531	3462	missing	annual_physical	65	2026-10-12	3	\N
3532	3463	missing	annual_physical	65	2026-10-12	3	\N
3533	3464	missing	annual_physical	65	2026-10-12	3	\N
3534	3465	missing	annual_physical	65	2026-10-12	3	\N
3535	3466	missing	annual_physical	65	2026-10-12	3	\N
3536	3467	missing	annual_physical	65	2026-10-12	3	\N
3537	3468	missing	annual_physical	65	2026-10-12	3	\N
3538	3469	missing	annual_physical	65	2026-10-12	3	\N
3539	3470	missing	annual_physical	65	2026-10-12	3	\N
3540	3471	missing	annual_physical	65	2026-10-12	3	\N
3541	3472	missing	annual_physical	65	2026-10-12	3	\N
3542	3473	missing	annual_physical	65	2026-10-12	3	\N
3543	3474	missing	annual_physical	65	2026-10-12	3	\N
3544	3475	missing	annual_physical	65	2026-10-12	3	\N
3545	3476	missing	annual_physical	65	2026-10-12	3	\N
3546	3477	missing	annual_physical	65	2026-10-12	3	\N
3547	3478	missing	annual_physical	65	2026-10-12	3	\N
3548	3479	missing	annual_physical	65	2026-10-12	3	\N
3549	3480	missing	annual_physical	65	2026-10-12	3	\N
3550	3481	missing	annual_physical	65	2026-10-12	3	\N
3551	3482	missing	annual_physical	65	2026-10-12	3	\N
3552	3483	missing	annual_physical	65	2026-10-12	3	\N
3553	3484	missing	annual_physical	65	2026-10-12	3	\N
3554	3485	missing	annual_physical	65	2026-10-12	3	\N
3555	3486	missing	annual_physical	65	2026-10-12	3	\N
3556	3487	missing	annual_physical	65	2026-10-12	3	\N
3557	3488	missing	annual_physical	65	2026-10-12	3	\N
3558	3489	missing	annual_physical	65	2026-10-12	3	\N
3559	3490	missing	annual_physical	65	2026-10-12	3	\N
3560	3491	missing	annual_physical	65	2026-10-12	3	\N
3561	3492	missing	annual_physical	65	2026-10-12	3	\N
3562	3493	missing	annual_physical	65	2026-10-12	3	\N
3563	3494	missing	annual_physical	65	2026-10-12	3	\N
3564	3495	missing	annual_physical	65	2026-10-12	3	\N
3565	3496	missing	annual_physical	65	2026-10-12	3	\N
3566	3497	missing	annual_physical	65	2026-10-12	3	\N
3567	3498	missing	annual_physical	65	2026-10-12	3	\N
3568	3499	missing	annual_physical	65	2026-10-12	3	\N
3569	3500	missing	annual_physical	65	2026-10-12	3	\N
3570	3501	missing	annual_physical	65	2026-10-12	3	\N
3571	3502	missing	annual_physical	65	2026-10-12	3	\N
3572	3503	missing	annual_physical	65	2026-10-12	3	\N
3573	3504	missing	annual_physical	65	2026-10-12	3	\N
3574	3505	missing	annual_physical	65	2026-10-12	3	\N
3575	3506	missing	annual_physical	65	2026-10-12	3	\N
3576	3507	missing	annual_physical	65	2026-10-12	3	\N
3577	3508	missing	annual_physical	65	2026-10-12	3	\N
3578	3509	missing	annual_physical	65	2026-10-12	3	\N
3579	3510	missing	annual_physical	65	2026-10-12	3	\N
3580	3511	missing	annual_physical	65	2026-10-12	3	\N
3581	3512	missing	annual_physical	65	2026-10-12	3	\N
3582	3513	missing	annual_physical	65	2026-10-12	3	\N
3583	3514	missing	annual_physical	65	2026-10-12	3	\N
3584	3515	missing	annual_physical	65	2026-10-12	3	\N
3585	3516	missing	annual_physical	65	2026-10-12	3	\N
3586	3517	missing	annual_physical	65	2026-10-12	3	\N
3587	3518	missing	annual_physical	65	2026-10-12	3	\N
3588	3519	missing	annual_physical	65	2026-10-12	3	\N
3589	3520	missing	annual_physical	65	2026-10-12	3	\N
3590	3521	missing	annual_physical	65	2026-10-12	3	\N
3591	3522	missing	annual_physical	65	2026-10-12	3	\N
3592	3523	missing	annual_physical	65	2026-10-12	3	\N
3593	3524	missing	annual_physical	65	2026-10-12	3	\N
3594	3525	missing	annual_physical	65	2026-10-12	3	\N
3595	3526	missing	annual_physical	65	2026-10-12	3	\N
3596	3527	missing	annual_physical	65	2026-10-12	3	\N
3597	3528	missing	annual_physical	65	2026-10-12	3	\N
3598	3529	missing	annual_physical	65	2026-10-12	3	\N
3599	3530	missing	annual_physical	65	2026-10-12	3	\N
3600	3531	missing	annual_physical	65	2026-10-12	3	\N
3601	3532	missing	annual_physical	65	2026-10-12	3	\N
3602	3533	missing	annual_physical	65	2026-10-12	3	\N
3603	3534	missing	annual_physical	65	2026-10-12	3	\N
3604	3535	missing	annual_physical	65	2026-10-12	3	\N
3605	3536	missing	annual_physical	65	2026-10-12	3	\N
3606	3537	missing	annual_physical	65	2026-10-12	3	\N
3607	3538	missing	annual_physical	65	2026-10-12	3	\N
3608	3539	missing	annual_physical	65	2026-10-12	3	\N
3609	3540	missing	annual_physical	65	2026-10-12	3	\N
3610	3541	missing	annual_physical	65	2026-10-12	3	\N
3611	3542	missing	annual_physical	65	2026-10-12	3	\N
3612	3543	missing	annual_physical	65	2026-10-12	3	\N
3613	3544	missing	annual_physical	65	2026-10-12	3	\N
3614	3545	missing	annual_physical	65	2026-10-12	3	\N
3615	3546	missing	annual_physical	65	2026-10-12	3	\N
3616	3547	missing	annual_physical	65	2026-10-12	3	\N
3617	3548	missing	annual_physical	65	2026-10-12	3	\N
3618	3549	missing	annual_physical	65	2026-10-12	3	\N
3619	3550	missing	annual_physical	65	2026-10-12	3	\N
3620	3551	missing	annual_physical	65	2026-10-12	3	\N
3621	3552	missing	annual_physical	65	2026-10-12	3	\N
3622	3553	missing	annual_physical	65	2026-10-12	3	\N
3623	3554	missing	annual_physical	65	2026-10-12	3	\N
3624	3555	missing	annual_physical	65	2026-10-12	3	\N
3625	3556	missing	annual_physical	65	2026-10-12	3	\N
3626	3557	missing	annual_physical	65	2026-10-12	3	\N
3627	3558	missing	annual_physical	65	2026-10-12	3	\N
3628	3559	missing	annual_physical	65	2026-10-12	3	\N
3629	3560	borrowed	annual_physical	65	2026-10-12	3	\N
3630	3561	missing	annual_physical	65	2026-10-12	3	\N
3631	3562	missing	annual_physical	65	2026-10-12	3	\N
3632	3563	missing	annual_physical	65	2026-10-12	3	\N
3633	3564	missing	annual_physical	65	2026-10-12	3	\N
3634	3565	missing	annual_physical	65	2026-10-12	3	\N
3635	3566	missing	annual_physical	65	2026-10-12	3	\N
3636	3567	missing	annual_physical	65	2026-10-12	3	\N
3637	3568	missing	annual_physical	65	2026-10-12	3	\N
3638	3569	missing	annual_physical	65	2026-10-12	3	\N
3639	3570	missing	annual_physical	65	2026-10-12	3	\N
3640	3571	missing	annual_physical	65	2026-10-12	3	\N
3641	3572	missing	annual_physical	65	2026-10-12	3	\N
3642	3573	missing	annual_physical	65	2026-10-12	3	\N
3643	3574	missing	annual_physical	65	2026-10-12	3	\N
3644	3575	missing	annual_physical	65	2026-10-12	3	\N
3645	3576	missing	annual_physical	65	2026-10-12	3	\N
3646	3577	missing	annual_physical	65	2026-10-12	3	\N
3647	3578	missing	annual_physical	65	2026-10-12	3	\N
3648	3579	missing	annual_physical	65	2026-10-12	3	\N
3649	3580	missing	annual_physical	65	2026-10-12	3	\N
3650	3581	missing	annual_physical	65	2026-10-12	3	\N
3651	3582	missing	annual_physical	65	2026-10-12	3	\N
3652	3583	missing	annual_physical	65	2026-10-12	3	\N
3653	3584	missing	annual_physical	65	2026-10-12	3	\N
3654	3585	missing	annual_physical	65	2026-10-12	3	\N
3655	3586	missing	annual_physical	65	2026-10-12	3	\N
3656	3587	missing	annual_physical	65	2026-10-12	3	\N
3657	3588	missing	annual_physical	65	2026-10-12	3	\N
3658	3589	missing	annual_physical	65	2026-10-12	3	\N
3659	3590	missing	annual_physical	65	2026-10-12	3	\N
3660	3591	missing	annual_physical	65	2026-10-12	3	\N
3661	3592	missing	annual_physical	65	2026-10-12	3	\N
3662	3593	missing	annual_physical	65	2026-10-12	3	\N
3663	3594	missing	annual_physical	65	2026-10-12	3	\N
3664	3595	missing	annual_physical	65	2026-10-12	3	\N
3665	3596	missing	annual_physical	65	2026-10-12	3	\N
3666	3597	missing	annual_physical	65	2026-10-12	3	\N
3667	3598	missing	annual_physical	65	2026-10-12	3	\N
3668	3599	missing	annual_physical	65	2026-10-12	3	\N
3669	3600	missing	annual_physical	65	2026-10-12	3	\N
3670	3601	missing	annual_physical	65	2026-10-12	3	\N
3671	3602	missing	annual_physical	65	2026-10-12	3	\N
3672	3603	missing	annual_physical	65	2026-10-12	3	\N
3673	3604	missing	annual_physical	65	2026-10-12	3	\N
3674	3605	missing	annual_physical	65	2026-10-12	3	\N
3675	3606	missing	annual_physical	65	2026-10-12	3	\N
3676	3607	missing	annual_physical	65	2026-10-12	3	\N
3677	3608	missing	annual_physical	65	2026-10-12	3	\N
3678	3609	missing	annual_physical	65	2026-10-12	3	\N
3679	3610	missing	annual_physical	65	2026-10-12	3	\N
3680	3611	missing	annual_physical	65	2026-10-12	3	\N
3681	3612	missing	annual_physical	65	2026-10-12	3	\N
3682	3613	missing	annual_physical	65	2026-10-12	3	\N
3683	3614	missing	annual_physical	65	2026-10-12	3	\N
3684	3615	missing	annual_physical	65	2026-10-12	3	\N
3685	3616	missing	annual_physical	65	2026-10-12	3	\N
3686	3617	missing	annual_physical	65	2026-10-12	3	\N
3687	3618	missing	annual_physical	65	2026-10-12	3	\N
3688	3619	missing	annual_physical	65	2026-10-12	3	\N
3689	3620	missing	annual_physical	65	2026-10-12	3	\N
3690	3621	missing	annual_physical	65	2026-10-12	3	\N
3691	3622	missing	annual_physical	65	2026-10-12	3	\N
3692	3623	missing	annual_physical	65	2026-10-12	3	\N
3693	3624	missing	annual_physical	65	2026-10-12	3	\N
3694	3625	missing	annual_physical	65	2026-10-12	3	\N
3695	3626	missing	annual_physical	65	2026-10-12	3	\N
3696	3627	missing	annual_physical	65	2026-10-12	3	\N
3697	3628	missing	annual_physical	65	2026-10-12	3	\N
3698	3629	missing	annual_physical	65	2026-10-12	3	\N
3699	3630	missing	annual_physical	65	2026-10-12	3	\N
3700	3631	missing	annual_physical	65	2026-10-12	3	\N
3701	3632	missing	annual_physical	65	2026-10-12	3	\N
3702	3633	missing	annual_physical	65	2026-10-12	3	\N
3703	3634	missing	annual_physical	65	2026-10-12	3	\N
3704	3635	missing	annual_physical	65	2026-10-12	3	\N
3705	3636	missing	annual_physical	65	2026-10-12	3	\N
3706	3637	missing	annual_physical	65	2026-10-12	3	\N
3707	3638	missing	annual_physical	65	2026-10-12	3	\N
3708	3639	missing	annual_physical	65	2026-10-12	3	\N
3709	3640	missing	annual_physical	65	2026-10-12	3	\N
3710	3641	missing	annual_physical	65	2026-10-12	3	\N
3711	3642	missing	annual_physical	65	2026-10-12	3	\N
3712	3643	missing	annual_physical	65	2026-10-12	3	\N
3713	3644	missing	annual_physical	65	2026-10-12	3	\N
3714	3645	missing	annual_physical	65	2026-10-12	3	\N
3715	3646	missing	annual_physical	65	2026-10-12	3	\N
3716	3647	missing	annual_physical	65	2026-10-12	3	\N
3717	3648	missing	annual_physical	65	2026-10-12	3	\N
3718	3649	missing	annual_physical	65	2026-10-12	3	\N
3719	3650	missing	annual_physical	65	2026-10-12	3	\N
3720	3651	missing	annual_physical	65	2026-10-12	3	\N
3721	3652	missing	annual_physical	65	2026-10-12	3	\N
3722	3653	missing	annual_physical	65	2026-10-12	3	\N
3723	3654	missing	annual_physical	65	2026-10-12	3	\N
3724	3655	missing	annual_physical	65	2026-10-12	3	\N
3725	3656	missing	annual_physical	65	2026-10-12	3	\N
3726	3657	missing	annual_physical	65	2026-10-12	3	\N
3727	3658	missing	annual_physical	65	2026-10-12	3	\N
3728	3659	missing	annual_physical	65	2026-10-12	3	\N
3729	3660	missing	annual_physical	65	2026-10-12	3	\N
3730	3661	missing	annual_physical	65	2026-10-12	3	\N
3731	3662	missing	annual_physical	65	2026-10-12	3	\N
3732	3663	missing	annual_physical	65	2026-10-12	3	\N
3733	3664	missing	annual_physical	65	2026-10-12	3	\N
3734	3665	missing	annual_physical	65	2026-10-12	3	\N
3735	3666	missing	annual_physical	65	2026-10-12	3	\N
3736	3667	missing	annual_physical	65	2026-10-12	3	\N
3737	3668	missing	annual_physical	65	2026-10-12	3	\N
3738	3669	missing	annual_physical	65	2026-10-12	3	\N
3739	3670	missing	annual_physical	65	2026-10-12	3	\N
3740	3671	missing	annual_physical	65	2026-10-12	3	\N
3741	3672	missing	annual_physical	65	2026-10-12	3	\N
3742	3673	missing	annual_physical	65	2026-10-12	3	\N
3743	3674	missing	annual_physical	65	2026-10-12	3	\N
3744	3675	missing	annual_physical	65	2026-10-12	3	\N
3745	3676	missing	annual_physical	65	2026-10-12	3	\N
3746	3677	missing	annual_physical	65	2026-10-12	3	\N
3747	3678	missing	annual_physical	65	2026-10-12	3	\N
3748	3679	missing	annual_physical	65	2026-10-12	3	\N
3749	3680	missing	annual_physical	65	2026-10-12	3	\N
3750	3681	missing	annual_physical	65	2026-10-12	3	\N
3751	3682	missing	annual_physical	65	2026-10-12	3	\N
3752	3683	missing	annual_physical	65	2026-10-12	3	\N
3753	3684	missing	annual_physical	65	2026-10-12	3	\N
3754	3685	missing	annual_physical	65	2026-10-12	3	\N
3755	3686	missing	annual_physical	65	2026-10-12	3	\N
3756	3687	missing	annual_physical	65	2026-10-12	3	\N
3757	3688	missing	annual_physical	65	2026-10-12	3	\N
3758	3689	missing	annual_physical	65	2026-10-12	3	\N
3759	3690	missing	annual_physical	65	2026-10-12	3	\N
3760	3691	missing	annual_physical	65	2026-10-12	3	\N
3761	3692	missing	annual_physical	65	2026-10-12	3	\N
3762	3693	missing	annual_physical	65	2026-10-12	3	\N
3763	3694	missing	annual_physical	65	2026-10-12	3	\N
3764	3695	missing	annual_physical	65	2026-10-12	3	\N
3765	3696	missing	annual_physical	65	2026-10-12	3	\N
3766	3697	missing	annual_physical	65	2026-10-12	3	\N
3767	3698	missing	annual_physical	65	2026-10-12	3	\N
3768	3699	missing	annual_physical	65	2026-10-12	3	\N
3769	3700	missing	annual_physical	65	2026-10-12	3	\N
3770	3701	missing	annual_physical	65	2026-10-12	3	\N
3771	3702	missing	annual_physical	65	2026-10-12	3	\N
3772	3703	missing	annual_physical	65	2026-10-12	3	\N
3773	3704	missing	annual_physical	65	2026-10-12	3	\N
3774	3705	missing	annual_physical	65	2026-10-12	3	\N
3775	3706	missing	annual_physical	65	2026-10-12	3	\N
3776	3707	missing	annual_physical	65	2026-10-12	3	\N
3777	3708	missing	annual_physical	65	2026-10-12	3	\N
3778	3709	missing	annual_physical	65	2026-10-12	3	\N
3779	3710	missing	annual_physical	65	2026-10-12	3	\N
3780	3711	missing	annual_physical	65	2026-10-12	3	\N
3781	3712	missing	annual_physical	65	2026-10-12	3	\N
3782	3713	missing	annual_physical	65	2026-10-12	3	\N
3783	3714	missing	annual_physical	65	2026-10-12	3	\N
3784	3715	missing	annual_physical	65	2026-10-12	3	\N
3785	3716	missing	annual_physical	65	2026-10-12	3	\N
3786	3717	missing	annual_physical	65	2026-10-12	3	\N
3787	3718	missing	annual_physical	65	2026-10-12	3	\N
3788	3719	missing	annual_physical	65	2026-10-12	3	\N
3789	3720	missing	annual_physical	65	2026-10-12	3	\N
3790	3721	missing	annual_physical	65	2026-10-12	3	\N
3791	3722	missing	annual_physical	65	2026-10-12	3	\N
3792	3723	missing	annual_physical	65	2026-10-12	3	\N
3793	3724	missing	annual_physical	65	2026-10-12	3	\N
3794	3725	missing	annual_physical	65	2026-10-12	3	\N
3795	3726	missing	annual_physical	65	2026-10-12	3	\N
3796	3727	missing	annual_physical	65	2026-10-12	3	\N
3797	3728	missing	annual_physical	65	2026-10-12	3	\N
3798	3729	missing	annual_physical	65	2026-10-12	3	\N
3799	3730	missing	annual_physical	65	2026-10-12	3	\N
3800	3731	missing	annual_physical	65	2026-10-12	3	\N
3801	3732	missing	annual_physical	65	2026-10-12	3	\N
3802	3733	missing	annual_physical	65	2026-10-12	3	\N
3803	3734	missing	annual_physical	65	2026-10-12	3	\N
3804	3735	missing	annual_physical	65	2026-10-12	3	\N
3805	3736	missing	annual_physical	65	2026-10-12	3	\N
3806	3737	missing	annual_physical	65	2026-10-12	3	\N
3807	3738	missing	annual_physical	65	2026-10-12	3	\N
3808	3739	missing	annual_physical	65	2026-10-12	3	\N
3809	3740	missing	annual_physical	65	2026-10-12	3	\N
3810	3741	missing	annual_physical	65	2026-10-12	3	\N
3811	3742	missing	annual_physical	65	2026-10-12	3	\N
3812	3743	missing	annual_physical	65	2026-10-12	3	\N
3813	3744	missing	annual_physical	65	2026-10-12	3	\N
3814	3745	missing	annual_physical	65	2026-10-12	3	\N
3815	3746	missing	annual_physical	65	2026-10-12	3	\N
3816	3747	missing	annual_physical	65	2026-10-12	3	\N
3817	3748	missing	annual_physical	65	2026-10-12	3	\N
3818	3749	missing	annual_physical	65	2026-10-12	3	\N
3819	3750	missing	annual_physical	65	2026-10-12	3	\N
3820	3751	missing	annual_physical	65	2026-10-12	3	\N
3821	3752	missing	annual_physical	65	2026-10-12	3	\N
3822	3753	missing	annual_physical	65	2026-10-12	3	\N
3823	3754	missing	annual_physical	65	2026-10-12	3	\N
3824	3755	missing	annual_physical	65	2026-10-12	3	\N
3825	3756	missing	annual_physical	65	2026-10-12	3	\N
3826	3757	missing	annual_physical	65	2026-10-12	3	\N
3827	3758	missing	annual_physical	65	2026-10-12	3	\N
3828	3759	missing	annual_physical	65	2026-10-12	3	\N
3829	3760	missing	annual_physical	65	2026-10-12	3	\N
3830	3761	missing	annual_physical	65	2026-10-12	3	\N
3831	3762	missing	annual_physical	65	2026-10-12	3	\N
3832	3763	missing	annual_physical	65	2026-10-12	3	\N
3833	3764	missing	annual_physical	65	2026-10-12	3	\N
3834	3765	missing	annual_physical	65	2026-10-12	3	\N
3835	3766	missing	annual_physical	65	2026-10-12	3	\N
3836	3767	missing	annual_physical	65	2026-10-12	3	\N
3837	3768	missing	annual_physical	65	2026-10-12	3	\N
3838	3769	missing	annual_physical	65	2026-10-12	3	\N
3839	3770	missing	annual_physical	65	2026-10-12	3	\N
3840	3771	missing	annual_physical	65	2026-10-12	3	\N
3841	3772	missing	annual_physical	65	2026-10-12	3	\N
3842	3773	missing	annual_physical	65	2026-10-12	3	\N
3843	3774	missing	annual_physical	65	2026-10-12	3	\N
3844	3775	missing	annual_physical	65	2026-10-12	3	\N
3845	3776	missing	annual_physical	65	2026-10-12	3	\N
3846	3777	missing	annual_physical	65	2026-10-12	3	\N
3847	3778	missing	annual_physical	65	2026-10-12	3	\N
3848	3779	missing	annual_physical	65	2026-10-12	3	\N
3849	3780	missing	annual_physical	65	2026-10-12	3	\N
3850	3781	missing	annual_physical	65	2026-10-12	3	\N
3851	3782	missing	annual_physical	65	2026-10-12	3	\N
3852	3783	missing	annual_physical	65	2026-10-12	3	\N
3853	3784	missing	annual_physical	65	2026-10-12	3	\N
3854	3785	missing	annual_physical	65	2026-10-12	3	\N
3855	3786	missing	annual_physical	65	2026-10-12	3	\N
3856	3787	missing	annual_physical	65	2026-10-12	3	\N
3857	3788	missing	annual_physical	65	2026-10-12	3	\N
3858	3789	missing	annual_physical	65	2026-10-12	3	\N
3859	3790	missing	annual_physical	65	2026-10-12	3	\N
3860	3791	missing	annual_physical	65	2026-10-12	3	\N
3861	3792	missing	annual_physical	65	2026-10-12	3	\N
3862	3793	missing	annual_physical	65	2026-10-12	3	\N
3863	3794	missing	annual_physical	65	2026-10-12	3	\N
3864	3795	missing	annual_physical	65	2026-10-12	3	\N
3865	3796	missing	annual_physical	65	2026-10-12	3	\N
3866	3797	missing	annual_physical	65	2026-10-12	3	\N
3867	3798	missing	annual_physical	65	2026-10-12	3	\N
3868	3799	missing	annual_physical	65	2026-10-12	3	\N
3869	3800	missing	annual_physical	65	2026-10-12	3	\N
3870	3801	missing	annual_physical	65	2026-10-12	3	\N
3871	3802	missing	annual_physical	65	2026-10-12	3	\N
3872	3803	missing	annual_physical	65	2026-10-12	3	\N
3873	3804	missing	annual_physical	65	2026-10-12	3	\N
3874	3805	missing	annual_physical	65	2026-10-12	3	\N
3875	3806	missing	annual_physical	65	2026-10-12	3	\N
3876	3807	missing	annual_physical	65	2026-10-12	3	\N
3877	3808	missing	annual_physical	65	2026-10-12	3	\N
3878	3809	missing	annual_physical	65	2026-10-12	3	\N
3879	3810	missing	annual_physical	65	2026-10-12	3	\N
3880	3811	missing	annual_physical	65	2026-10-12	3	\N
3881	3812	missing	annual_physical	65	2026-10-12	3	\N
3882	3813	missing	annual_physical	65	2026-10-12	3	\N
3883	3814	missing	annual_physical	65	2026-10-12	3	\N
3884	3815	missing	annual_physical	65	2026-10-12	3	\N
3885	3816	missing	annual_physical	65	2026-10-12	3	\N
3886	3817	missing	annual_physical	65	2026-10-12	3	\N
3887	3818	missing	annual_physical	65	2026-10-12	3	\N
3888	3819	missing	annual_physical	65	2026-10-12	3	\N
3889	3820	missing	annual_physical	65	2026-10-12	3	\N
3890	3821	missing	annual_physical	65	2026-10-12	3	\N
3891	3822	missing	annual_physical	65	2026-10-12	3	\N
3892	3823	missing	annual_physical	65	2026-10-12	3	\N
3893	3824	missing	annual_physical	65	2026-10-12	3	\N
3894	3825	missing	annual_physical	65	2026-10-12	3	\N
3895	3826	missing	annual_physical	65	2026-10-12	3	\N
3896	3827	missing	annual_physical	65	2026-10-12	3	\N
3897	3828	missing	annual_physical	65	2026-10-12	3	\N
3898	3829	missing	annual_physical	65	2026-10-12	3	\N
3899	3830	missing	annual_physical	65	2026-10-12	3	\N
3900	3831	missing	annual_physical	65	2026-10-12	3	\N
3901	3832	missing	annual_physical	65	2026-10-12	3	\N
3902	3833	missing	annual_physical	65	2026-10-12	3	\N
3903	3834	missing	annual_physical	65	2026-10-12	3	\N
3904	3835	missing	annual_physical	65	2026-10-12	3	\N
3905	3836	missing	annual_physical	65	2026-10-12	3	\N
3906	3837	missing	annual_physical	65	2026-10-12	3	\N
3907	3838	missing	annual_physical	65	2026-10-12	3	\N
3908	3839	missing	annual_physical	65	2026-10-12	3	\N
3909	3840	missing	annual_physical	65	2026-10-12	3	\N
3910	3841	missing	annual_physical	65	2026-10-12	3	\N
3911	3842	missing	annual_physical	65	2026-10-12	3	\N
3912	3843	missing	annual_physical	65	2026-10-12	3	\N
3913	3844	missing	annual_physical	65	2026-10-12	3	\N
3914	3845	missing	annual_physical	65	2026-10-12	3	\N
3915	3846	missing	annual_physical	65	2026-10-12	3	\N
3916	3847	missing	annual_physical	65	2026-10-12	3	\N
3917	3848	missing	annual_physical	65	2026-10-12	3	\N
3918	3849	missing	annual_physical	65	2026-10-12	3	\N
3919	3850	missing	annual_physical	65	2026-10-12	3	\N
3920	3851	missing	annual_physical	65	2026-10-12	3	\N
3921	3852	missing	annual_physical	65	2026-10-12	3	\N
3922	3853	missing	annual_physical	65	2026-10-12	3	\N
3923	3854	missing	annual_physical	65	2026-10-12	3	\N
3924	3855	missing	annual_physical	65	2026-10-12	3	\N
3925	3856	missing	annual_physical	65	2026-10-12	3	\N
3926	3857	missing	annual_physical	65	2026-10-12	3	\N
3927	3858	missing	annual_physical	65	2026-10-12	3	\N
3928	3859	missing	annual_physical	65	2026-10-12	3	\N
3929	3860	missing	annual_physical	65	2026-10-12	3	\N
3930	3861	missing	annual_physical	65	2026-10-12	3	\N
3931	3862	missing	annual_physical	65	2026-10-12	3	\N
3932	3863	missing	annual_physical	65	2026-10-12	3	\N
3933	3864	missing	annual_physical	65	2026-10-12	3	\N
3934	3865	missing	annual_physical	65	2026-10-12	3	\N
3935	3866	missing	annual_physical	65	2026-10-12	3	\N
3936	3867	missing	annual_physical	65	2026-10-12	3	\N
3937	3868	missing	annual_physical	65	2026-10-12	3	\N
3938	3869	missing	annual_physical	65	2026-10-12	3	\N
3939	3870	missing	annual_physical	65	2026-10-12	3	\N
3940	3871	missing	annual_physical	65	2026-10-12	3	\N
3941	3872	missing	annual_physical	65	2026-10-12	3	\N
3942	3873	missing	annual_physical	65	2026-10-12	3	\N
3943	3874	missing	annual_physical	65	2026-10-12	3	\N
3944	3875	missing	annual_physical	65	2026-10-12	3	\N
3945	3876	missing	annual_physical	65	2026-10-12	3	\N
3946	3877	missing	annual_physical	65	2026-10-12	3	\N
3947	3878	missing	annual_physical	65	2026-10-12	3	\N
3948	3879	missing	annual_physical	65	2026-10-12	3	\N
3949	3880	missing	annual_physical	65	2026-10-12	3	\N
3950	3881	missing	annual_physical	65	2026-10-12	3	\N
3951	3882	missing	annual_physical	65	2026-10-12	3	\N
3952	3883	missing	annual_physical	65	2026-10-12	3	\N
3953	3884	missing	annual_physical	65	2026-10-12	3	\N
3954	3885	missing	annual_physical	65	2026-10-12	3	\N
3955	3886	missing	annual_physical	65	2026-10-12	3	\N
3956	3887	missing	annual_physical	65	2026-10-12	3	\N
3957	3888	missing	annual_physical	65	2026-10-12	3	\N
3958	3889	missing	annual_physical	65	2026-10-12	3	\N
3959	3890	missing	annual_physical	65	2026-10-12	3	\N
3960	3891	missing	annual_physical	65	2026-10-12	3	\N
3961	3892	missing	annual_physical	65	2026-10-12	3	\N
3962	3893	missing	annual_physical	65	2026-10-12	3	\N
3963	3894	missing	annual_physical	65	2026-10-12	3	\N
3964	3895	missing	annual_physical	65	2026-10-12	3	\N
3965	3896	missing	annual_physical	65	2026-10-12	3	\N
3966	3897	missing	annual_physical	65	2026-10-12	3	\N
3967	3898	missing	annual_physical	65	2026-10-12	3	\N
3968	3899	missing	annual_physical	65	2026-10-12	3	\N
3969	3900	missing	annual_physical	65	2026-10-12	3	\N
3970	3901	missing	annual_physical	65	2026-10-12	3	\N
3971	3902	missing	annual_physical	65	2026-10-12	3	\N
3972	3903	missing	annual_physical	65	2026-10-12	3	\N
3973	3904	missing	annual_physical	65	2026-10-12	3	\N
3974	3905	missing	annual_physical	65	2026-10-12	3	\N
3975	3906	missing	annual_physical	65	2026-10-12	3	\N
3976	3907	missing	annual_physical	65	2026-10-12	3	\N
3977	3908	missing	annual_physical	65	2026-10-12	3	\N
3978	3909	missing	annual_physical	65	2026-10-12	3	\N
3979	3910	missing	annual_physical	65	2026-10-12	3	\N
3980	3911	missing	annual_physical	65	2026-10-12	3	\N
3981	3912	missing	annual_physical	65	2026-10-12	3	\N
3982	3913	missing	annual_physical	65	2026-10-12	3	\N
3983	3914	missing	annual_physical	65	2026-10-12	3	\N
3984	3915	missing	annual_physical	65	2026-10-12	3	\N
3985	3916	missing	annual_physical	65	2026-10-12	3	\N
3986	3917	missing	annual_physical	65	2026-10-12	3	\N
3987	3918	missing	annual_physical	65	2026-10-12	3	\N
3988	3919	missing	annual_physical	65	2026-10-12	3	\N
3989	3920	missing	annual_physical	65	2026-10-12	3	\N
3990	3921	missing	annual_physical	65	2026-10-12	3	\N
3991	3922	missing	annual_physical	65	2026-10-12	3	\N
3992	3923	missing	annual_physical	65	2026-10-12	3	\N
3993	3924	missing	annual_physical	65	2026-10-12	3	\N
3994	3925	missing	annual_physical	65	2026-10-12	3	\N
3995	3926	missing	annual_physical	65	2026-10-12	3	\N
3996	3927	missing	annual_physical	65	2026-10-12	3	\N
3997	3928	missing	annual_physical	65	2026-10-12	3	\N
3998	3929	missing	annual_physical	65	2026-10-12	3	\N
3999	3930	missing	annual_physical	65	2026-10-12	3	\N
4000	3931	missing	annual_physical	65	2026-10-12	3	\N
4001	3932	missing	annual_physical	65	2026-10-12	3	\N
4002	3933	missing	annual_physical	65	2026-10-12	3	\N
4003	3934	missing	annual_physical	65	2026-10-12	3	\N
4004	3935	missing	annual_physical	65	2026-10-12	3	\N
4005	3936	missing	annual_physical	65	2026-10-12	3	\N
4006	3937	missing	annual_physical	65	2026-10-12	3	\N
4007	3938	missing	annual_physical	65	2026-10-12	3	\N
4008	3939	missing	annual_physical	65	2026-10-12	3	\N
4009	3940	missing	annual_physical	65	2026-10-12	3	\N
4010	3941	missing	annual_physical	65	2026-10-12	3	\N
4011	3942	missing	annual_physical	65	2026-10-12	3	\N
4012	3943	missing	annual_physical	65	2026-10-12	3	\N
4013	3944	missing	annual_physical	65	2026-10-12	3	\N
4014	3945	missing	annual_physical	65	2026-10-12	3	\N
4015	3946	missing	annual_physical	65	2026-10-12	3	\N
4016	3947	missing	annual_physical	65	2026-10-12	3	\N
4017	3948	missing	annual_physical	65	2026-10-12	3	\N
4018	3949	missing	annual_physical	65	2026-10-12	3	\N
4019	3950	missing	annual_physical	65	2026-10-12	3	\N
4020	3951	missing	annual_physical	65	2026-10-12	3	\N
4021	3952	missing	annual_physical	65	2026-10-12	3	\N
4022	3953	missing	annual_physical	65	2026-10-12	3	\N
4023	3954	missing	annual_physical	65	2026-10-12	3	\N
4024	3955	missing	annual_physical	65	2026-10-12	3	\N
4025	3956	missing	annual_physical	65	2026-10-12	3	\N
4026	3957	missing	annual_physical	65	2026-10-12	3	\N
4027	3958	missing	annual_physical	65	2026-10-12	3	\N
4028	3959	missing	annual_physical	65	2026-10-12	3	\N
4029	3960	missing	annual_physical	65	2026-10-12	3	\N
4030	3961	missing	annual_physical	65	2026-10-12	3	\N
4031	3962	missing	annual_physical	65	2026-10-12	3	\N
4032	3963	missing	annual_physical	65	2026-10-12	3	\N
4033	3964	missing	annual_physical	65	2026-10-12	3	\N
4034	3965	missing	annual_physical	65	2026-10-12	3	\N
4035	3966	missing	annual_physical	65	2026-10-12	3	\N
4036	3967	missing	annual_physical	65	2026-10-12	3	\N
4037	3968	missing	annual_physical	65	2026-10-12	3	\N
4038	3969	missing	annual_physical	65	2026-10-12	3	\N
4039	3970	missing	annual_physical	65	2026-10-12	3	\N
4040	3971	missing	annual_physical	65	2026-10-12	3	\N
4041	3972	missing	annual_physical	65	2026-10-12	3	\N
4042	3973	missing	annual_physical	65	2026-10-12	3	\N
4043	3974	missing	annual_physical	65	2026-10-12	3	\N
4044	3975	missing	annual_physical	65	2026-10-12	3	\N
4045	3976	missing	annual_physical	65	2026-10-12	3	\N
4046	3977	missing	annual_physical	65	2026-10-12	3	\N
4047	3978	missing	annual_physical	65	2026-10-12	3	\N
4048	3979	missing	annual_physical	65	2026-10-12	3	\N
4049	3980	missing	annual_physical	65	2026-10-12	3	\N
4050	3981	missing	annual_physical	65	2026-10-12	3	\N
4051	3982	missing	annual_physical	65	2026-10-12	3	\N
4052	3983	missing	annual_physical	65	2026-10-12	3	\N
4053	3984	missing	annual_physical	65	2026-10-12	3	\N
4054	3985	missing	annual_physical	65	2026-10-12	3	\N
4055	3986	missing	annual_physical	65	2026-10-12	3	\N
4056	3987	missing	annual_physical	65	2026-10-12	3	\N
4057	3988	missing	annual_physical	65	2026-10-12	3	\N
4058	3989	missing	annual_physical	65	2026-10-12	3	\N
4059	3990	missing	annual_physical	65	2026-10-12	3	\N
4060	3991	missing	annual_physical	65	2026-10-12	3	\N
4061	3992	missing	annual_physical	65	2026-10-12	3	\N
4062	3993	missing	annual_physical	65	2026-10-12	3	\N
4063	3994	missing	annual_physical	65	2026-10-12	3	\N
4064	3995	missing	annual_physical	65	2026-10-12	3	\N
4065	3996	missing	annual_physical	65	2026-10-12	3	\N
4066	3997	missing	annual_physical	65	2026-10-12	3	\N
4067	3998	missing	annual_physical	65	2026-10-12	3	\N
4068	3999	missing	annual_physical	65	2026-10-12	3	\N
4069	4000	missing	annual_physical	65	2026-10-12	3	\N
4070	4001	missing	annual_physical	65	2026-10-12	3	\N
4071	4002	missing	annual_physical	65	2026-10-12	3	\N
4072	4003	missing	annual_physical	65	2026-10-12	3	\N
4073	4004	missing	annual_physical	65	2026-10-12	3	\N
4074	4005	missing	annual_physical	65	2026-10-12	3	\N
4075	4006	missing	annual_physical	65	2026-10-12	3	\N
4076	4007	missing	annual_physical	65	2026-10-12	3	\N
4077	4008	missing	annual_physical	65	2026-10-12	3	\N
4078	4009	missing	annual_physical	65	2026-10-12	3	\N
4079	4010	missing	annual_physical	65	2026-10-12	3	\N
4080	4011	missing	annual_physical	65	2026-10-12	3	\N
4081	4012	missing	annual_physical	65	2026-10-12	3	\N
4082	4013	missing	annual_physical	65	2026-10-12	3	\N
4083	4014	missing	annual_physical	65	2026-10-12	3	\N
4084	4015	missing	annual_physical	65	2026-10-12	3	\N
4085	4016	missing	annual_physical	65	2026-10-12	3	\N
4086	4017	missing	annual_physical	65	2026-10-12	3	\N
4087	4018	missing	annual_physical	65	2026-10-12	3	\N
4088	4019	missing	annual_physical	65	2026-10-12	3	\N
4089	4020	missing	annual_physical	65	2026-10-12	3	\N
4090	4021	missing	annual_physical	65	2026-10-12	3	\N
4091	4022	missing	annual_physical	65	2026-10-12	3	\N
4092	4023	missing	annual_physical	65	2026-10-12	3	\N
4093	4024	missing	annual_physical	65	2026-10-12	3	\N
4094	4025	missing	annual_physical	65	2026-10-12	3	\N
4095	4026	missing	annual_physical	65	2026-10-12	3	\N
4096	4027	missing	annual_physical	65	2026-10-12	3	\N
4097	4028	missing	annual_physical	65	2026-10-12	3	\N
4098	4029	missing	annual_physical	65	2026-10-12	3	\N
4099	4030	missing	annual_physical	65	2026-10-12	3	\N
4100	4031	missing	annual_physical	65	2026-10-12	3	\N
4101	4032	missing	annual_physical	65	2026-10-12	3	\N
4102	4033	missing	annual_physical	65	2026-10-12	3	\N
4103	4034	missing	annual_physical	65	2026-10-12	3	\N
4104	4035	missing	annual_physical	65	2026-10-12	3	\N
4105	4036	missing	annual_physical	65	2026-10-12	3	\N
4106	4037	missing	annual_physical	65	2026-10-12	3	\N
4107	4038	missing	annual_physical	65	2026-10-12	3	\N
4108	4039	missing	annual_physical	65	2026-10-12	3	\N
4109	4040	missing	annual_physical	65	2026-10-12	3	\N
4110	4041	missing	annual_physical	65	2026-10-12	3	\N
4111	4042	missing	annual_physical	65	2026-10-12	3	\N
4112	4043	missing	annual_physical	65	2026-10-12	3	\N
4113	4044	missing	annual_physical	65	2026-10-12	3	\N
4114	4045	missing	annual_physical	65	2026-10-12	3	\N
4115	4046	missing	annual_physical	65	2026-10-12	3	\N
4116	4047	missing	annual_physical	65	2026-10-12	3	\N
4117	4048	missing	annual_physical	65	2026-10-12	3	\N
4118	4049	missing	annual_physical	65	2026-10-12	3	\N
4119	4050	missing	annual_physical	65	2026-10-12	3	\N
4120	4051	missing	annual_physical	65	2026-10-12	3	\N
4121	4052	missing	annual_physical	65	2026-10-12	3	\N
4122	4053	missing	annual_physical	65	2026-10-12	3	\N
4123	4054	missing	annual_physical	65	2026-10-12	3	\N
4124	4055	missing	annual_physical	65	2026-10-12	3	\N
4125	4056	missing	annual_physical	65	2026-10-12	3	\N
4126	4057	missing	annual_physical	65	2026-10-12	3	\N
4127	4058	missing	annual_physical	65	2026-10-12	3	\N
4128	4059	missing	annual_physical	65	2026-10-12	3	\N
4129	4060	missing	annual_physical	65	2026-10-12	3	\N
4130	4061	missing	annual_physical	65	2026-10-12	3	\N
4131	4062	missing	annual_physical	65	2026-10-12	3	\N
4132	4063	missing	annual_physical	65	2026-10-12	3	\N
4133	4064	missing	annual_physical	65	2026-10-12	3	\N
4134	4065	missing	annual_physical	65	2026-10-12	3	\N
4135	4066	missing	annual_physical	65	2026-10-12	3	\N
4136	4067	missing	annual_physical	65	2026-10-12	3	\N
4137	4068	missing	annual_physical	65	2026-10-12	3	\N
4138	4069	missing	annual_physical	65	2026-10-12	3	\N
4139	4070	missing	annual_physical	65	2026-10-12	3	\N
4140	4071	missing	annual_physical	65	2026-10-12	3	\N
4141	4072	missing	annual_physical	65	2026-10-12	3	\N
4142	4073	missing	annual_physical	65	2026-10-12	3	\N
4143	4074	missing	annual_physical	65	2026-10-12	3	\N
4144	4075	missing	annual_physical	65	2026-10-12	3	\N
4145	4076	missing	annual_physical	65	2026-10-12	3	\N
4146	4077	missing	annual_physical	65	2026-10-12	3	\N
4147	4078	missing	annual_physical	65	2026-10-12	3	\N
4148	4079	missing	annual_physical	65	2026-10-12	3	\N
4149	4080	missing	annual_physical	65	2026-10-12	3	\N
4150	4081	missing	annual_physical	65	2026-10-12	3	\N
4151	4082	missing	annual_physical	65	2026-10-12	3	\N
4152	4083	missing	annual_physical	65	2026-10-12	3	\N
4153	4084	missing	annual_physical	65	2026-10-12	3	\N
4154	4085	missing	annual_physical	65	2026-10-12	3	\N
4155	4086	missing	annual_physical	65	2026-10-12	3	\N
4156	4087	missing	annual_physical	65	2026-10-12	3	\N
4157	4088	missing	annual_physical	65	2026-10-12	3	\N
4158	4089	missing	annual_physical	65	2026-10-12	3	\N
4159	4090	missing	annual_physical	65	2026-10-12	3	\N
4160	4091	missing	annual_physical	65	2026-10-12	3	\N
4161	4092	missing	annual_physical	65	2026-10-12	3	\N
4162	4093	missing	annual_physical	65	2026-10-12	3	\N
4163	4094	missing	annual_physical	65	2026-10-12	3	\N
4164	4095	missing	annual_physical	65	2026-10-12	3	\N
4165	4096	missing	annual_physical	65	2026-10-12	3	\N
4166	4097	missing	annual_physical	65	2026-10-12	3	\N
4167	4098	missing	annual_physical	65	2026-10-12	3	\N
4168	4099	missing	annual_physical	65	2026-10-12	3	\N
4169	4100	missing	annual_physical	65	2026-10-12	3	\N
4170	4101	missing	annual_physical	65	2026-10-12	3	\N
4171	4102	missing	annual_physical	65	2026-10-12	3	\N
4172	4103	missing	annual_physical	65	2026-10-12	3	\N
4173	4104	missing	annual_physical	65	2026-10-12	3	\N
4174	4105	missing	annual_physical	65	2026-10-12	3	\N
4175	4106	missing	annual_physical	65	2026-10-12	3	\N
4176	4107	missing	annual_physical	65	2026-10-12	3	\N
4177	4108	missing	annual_physical	65	2026-10-12	3	\N
4178	4109	missing	annual_physical	65	2026-10-12	3	\N
4179	4110	missing	annual_physical	65	2026-10-12	3	\N
4180	4111	missing	annual_physical	65	2026-10-12	3	\N
4181	4112	missing	annual_physical	65	2026-10-12	3	\N
4182	4113	missing	annual_physical	65	2026-10-12	3	\N
4183	4114	missing	annual_physical	65	2026-10-12	3	\N
4184	4115	missing	annual_physical	65	2026-10-12	3	\N
4185	4116	missing	annual_physical	65	2026-10-12	3	\N
4186	4117	missing	annual_physical	65	2026-10-12	3	\N
4187	4118	missing	annual_physical	65	2026-10-12	3	\N
4188	4119	missing	annual_physical	65	2026-10-12	3	\N
4189	4120	missing	annual_physical	65	2026-10-12	3	\N
4190	4121	missing	annual_physical	65	2026-10-12	3	\N
4191	4122	missing	annual_physical	65	2026-10-12	3	\N
4192	4123	missing	annual_physical	65	2026-10-12	3	\N
4193	4124	missing	annual_physical	65	2026-10-12	3	\N
4194	4125	missing	annual_physical	65	2026-10-12	3	\N
4195	4126	missing	annual_physical	65	2026-10-12	3	\N
4196	4127	missing	annual_physical	65	2026-10-12	3	\N
4197	4128	missing	annual_physical	65	2026-10-12	3	\N
4198	4129	missing	annual_physical	65	2026-10-12	3	\N
4199	4130	missing	annual_physical	65	2026-10-12	3	\N
4200	4131	missing	annual_physical	65	2026-10-12	3	\N
4201	4132	missing	annual_physical	65	2026-10-12	3	\N
4202	4133	missing	annual_physical	65	2026-10-12	3	\N
4203	4134	missing	annual_physical	65	2026-10-12	3	\N
4204	4135	missing	annual_physical	65	2026-10-12	3	\N
4205	4136	missing	annual_physical	65	2026-10-12	3	\N
4206	4137	missing	annual_physical	65	2026-10-12	3	\N
4207	4138	missing	annual_physical	65	2026-10-12	3	\N
4208	4139	missing	annual_physical	65	2026-10-12	3	\N
4209	4140	missing	annual_physical	65	2026-10-12	3	\N
4210	4141	missing	annual_physical	65	2026-10-12	3	\N
4211	4142	missing	annual_physical	65	2026-10-12	3	\N
4212	4143	missing	annual_physical	65	2026-10-12	3	\N
4213	4144	missing	annual_physical	65	2026-10-12	3	\N
4214	4145	missing	annual_physical	65	2026-10-12	3	\N
4215	4146	missing	annual_physical	65	2026-10-12	3	\N
4216	4147	missing	annual_physical	65	2026-10-12	3	\N
4217	4148	missing	annual_physical	65	2026-10-12	3	\N
4218	4149	missing	annual_physical	65	2026-10-12	3	\N
4219	4150	missing	annual_physical	65	2026-10-12	3	\N
4220	4151	missing	annual_physical	65	2026-10-12	3	\N
4221	4152	missing	annual_physical	65	2026-10-12	3	\N
4222	4153	missing	annual_physical	65	2026-10-12	3	\N
4223	4154	missing	annual_physical	65	2026-10-12	3	\N
4224	4155	missing	annual_physical	65	2026-10-12	3	\N
4225	4156	missing	annual_physical	65	2026-10-12	3	\N
4226	4157	missing	annual_physical	65	2026-10-12	3	\N
4227	4158	missing	annual_physical	65	2026-10-12	3	\N
4228	4159	missing	annual_physical	65	2026-10-12	3	\N
4229	4160	missing	annual_physical	65	2026-10-12	3	\N
4230	4161	missing	annual_physical	65	2026-10-12	3	\N
4231	4162	missing	annual_physical	65	2026-10-12	3	\N
4232	4163	missing	annual_physical	65	2026-10-12	3	\N
4233	4164	missing	annual_physical	65	2026-10-12	3	\N
4234	4165	missing	annual_physical	65	2026-10-12	3	\N
4235	4166	missing	annual_physical	65	2026-10-12	3	\N
4236	4167	missing	annual_physical	65	2026-10-12	3	\N
4237	4168	missing	annual_physical	65	2026-10-12	3	\N
4238	4169	missing	annual_physical	65	2026-10-12	3	\N
4239	4170	missing	annual_physical	65	2026-10-12	3	\N
4240	4171	missing	annual_physical	65	2026-10-12	3	\N
4241	4172	missing	annual_physical	65	2026-10-12	3	\N
4242	4173	missing	annual_physical	65	2026-10-12	3	\N
4243	4174	missing	annual_physical	65	2026-10-12	3	\N
4244	4175	missing	annual_physical	65	2026-10-12	3	\N
4245	4176	missing	annual_physical	65	2026-10-12	3	\N
4246	4177	missing	annual_physical	65	2026-10-12	3	\N
4247	4178	missing	annual_physical	65	2026-10-12	3	\N
4248	4179	missing	annual_physical	65	2026-10-12	3	\N
4249	4180	missing	annual_physical	65	2026-10-12	3	\N
4250	4181	missing	annual_physical	65	2026-10-12	3	\N
4251	4182	missing	annual_physical	65	2026-10-12	3	\N
4252	4183	missing	annual_physical	65	2026-10-12	3	\N
4253	4184	missing	annual_physical	65	2026-10-12	3	\N
4254	4185	missing	annual_physical	65	2026-10-12	3	\N
4255	4186	missing	annual_physical	65	2026-10-12	3	\N
4256	4187	missing	annual_physical	65	2026-10-12	3	\N
4257	4188	missing	annual_physical	65	2026-10-12	3	\N
4258	4189	missing	annual_physical	65	2026-10-12	3	\N
4259	4190	missing	annual_physical	65	2026-10-12	3	\N
4260	4191	missing	annual_physical	65	2026-10-12	3	\N
4261	4192	missing	annual_physical	65	2026-10-12	3	\N
4262	4193	missing	annual_physical	65	2026-10-12	3	\N
4263	4194	missing	annual_physical	65	2026-10-12	3	\N
4264	4195	missing	annual_physical	65	2026-10-12	3	\N
4265	4196	missing	annual_physical	65	2026-10-12	3	\N
4266	4197	missing	annual_physical	65	2026-10-12	3	\N
4267	4198	missing	annual_physical	65	2026-10-12	3	\N
4268	4199	missing	annual_physical	65	2026-10-12	3	\N
4269	4200	missing	annual_physical	65	2026-10-12	3	\N
4270	4201	missing	annual_physical	65	2026-10-12	3	\N
4271	4202	missing	annual_physical	65	2026-10-12	3	\N
4272	4203	missing	annual_physical	65	2026-10-12	3	\N
4273	4204	missing	annual_physical	65	2026-10-12	3	\N
4274	4205	missing	annual_physical	65	2026-10-12	3	\N
4275	4206	missing	annual_physical	65	2026-10-12	3	\N
4276	4207	missing	annual_physical	65	2026-10-12	3	\N
4277	4208	missing	annual_physical	65	2026-10-12	3	\N
4278	4209	missing	annual_physical	65	2026-10-12	3	\N
4279	4210	missing	annual_physical	65	2026-10-12	3	\N
4280	4211	missing	annual_physical	65	2026-10-12	3	\N
4281	4212	missing	annual_physical	65	2026-10-12	3	\N
4282	4213	missing	annual_physical	65	2026-10-12	3	\N
4283	4214	missing	annual_physical	65	2026-10-12	3	\N
4284	4215	missing	annual_physical	65	2026-10-12	3	\N
4285	4216	missing	annual_physical	65	2026-10-12	3	\N
4286	4217	missing	annual_physical	65	2026-10-12	3	\N
4287	4218	missing	annual_physical	65	2026-10-12	3	\N
4288	4219	missing	annual_physical	65	2026-10-12	3	\N
4289	4220	missing	annual_physical	65	2026-10-12	3	\N
4290	4221	missing	annual_physical	65	2026-10-12	3	\N
4291	4222	missing	annual_physical	65	2026-10-12	3	\N
4292	4223	missing	annual_physical	65	2026-10-12	3	\N
4293	4224	missing	annual_physical	65	2026-10-12	3	\N
4294	4225	missing	annual_physical	65	2026-10-12	3	\N
4295	4226	missing	annual_physical	65	2026-10-12	3	\N
4296	4227	missing	annual_physical	65	2026-10-12	3	\N
4297	4228	missing	annual_physical	65	2026-10-12	3	\N
4298	4229	missing	annual_physical	65	2026-10-12	3	\N
4299	4230	missing	annual_physical	65	2026-10-12	3	\N
4300	4231	missing	annual_physical	65	2026-10-12	3	\N
4301	4232	missing	annual_physical	65	2026-10-12	3	\N
4302	4233	missing	annual_physical	65	2026-10-12	3	\N
4303	4234	missing	annual_physical	65	2026-10-12	3	\N
4304	4235	missing	annual_physical	65	2026-10-12	3	\N
4305	4236	missing	annual_physical	65	2026-10-12	3	\N
4306	4237	missing	annual_physical	65	2026-10-12	3	\N
4307	4238	missing	annual_physical	65	2026-10-12	3	\N
4308	4239	missing	annual_physical	65	2026-10-12	3	\N
4309	4240	missing	annual_physical	65	2026-10-12	3	\N
4310	4241	missing	annual_physical	65	2026-10-12	3	\N
4311	4242	missing	annual_physical	65	2026-10-12	3	\N
4312	4243	missing	annual_physical	65	2026-10-12	3	\N
4313	4244	missing	annual_physical	65	2026-10-12	3	\N
4314	4245	missing	annual_physical	65	2026-10-12	3	\N
4315	4246	missing	annual_physical	65	2026-10-12	3	\N
4316	4247	missing	annual_physical	65	2026-10-12	3	\N
4317	4248	missing	annual_physical	65	2026-10-12	3	\N
4318	4249	missing	annual_physical	65	2026-10-12	3	\N
4319	4250	missing	annual_physical	65	2026-10-12	3	\N
4320	4251	missing	annual_physical	65	2026-10-12	3	\N
4321	4252	missing	annual_physical	65	2026-10-12	3	\N
4322	4253	missing	annual_physical	65	2026-10-12	3	\N
4323	4254	missing	annual_physical	65	2026-10-12	3	\N
4324	4255	missing	annual_physical	65	2026-10-12	3	\N
4325	4256	missing	annual_physical	65	2026-10-12	3	\N
4326	4257	missing	annual_physical	65	2026-10-12	3	\N
4327	4258	missing	annual_physical	65	2026-10-12	3	\N
4328	4259	missing	annual_physical	65	2026-10-12	3	\N
4329	4260	missing	annual_physical	65	2026-10-12	3	\N
4330	4261	missing	annual_physical	65	2026-10-12	3	\N
4331	4262	missing	annual_physical	65	2026-10-12	3	\N
4332	4263	missing	annual_physical	65	2026-10-12	3	\N
4333	4264	missing	annual_physical	65	2026-10-12	3	\N
4334	4265	missing	annual_physical	65	2026-10-12	3	\N
4335	4266	missing	annual_physical	65	2026-10-12	3	\N
4336	4267	missing	annual_physical	65	2026-10-12	3	\N
4337	4268	missing	annual_physical	65	2026-10-12	3	\N
4338	4269	missing	annual_physical	65	2026-10-12	3	\N
4339	4270	missing	annual_physical	65	2026-10-12	3	\N
4340	4271	missing	annual_physical	65	2026-10-12	3	\N
4341	4272	missing	annual_physical	65	2026-10-12	3	\N
4342	4273	missing	annual_physical	65	2026-10-12	3	\N
4343	4274	missing	annual_physical	65	2026-10-12	3	\N
4344	4275	missing	annual_physical	65	2026-10-12	3	\N
4345	4276	missing	annual_physical	65	2026-10-12	3	\N
4346	4277	missing	annual_physical	65	2026-10-12	3	\N
4347	4278	missing	annual_physical	65	2026-10-12	3	\N
4348	4279	missing	annual_physical	65	2026-10-12	3	\N
4349	4280	missing	annual_physical	65	2026-10-12	3	\N
4350	4281	missing	annual_physical	65	2026-10-12	3	\N
4351	4282	missing	annual_physical	65	2026-10-12	3	\N
4352	4283	missing	annual_physical	65	2026-10-12	3	\N
4353	4284	missing	annual_physical	65	2026-10-12	3	\N
4354	4285	missing	annual_physical	65	2026-10-12	3	\N
4355	4286	missing	annual_physical	65	2026-10-12	3	\N
4356	4287	missing	annual_physical	65	2026-10-12	3	\N
4357	4288	missing	annual_physical	65	2026-10-12	3	\N
4358	4289	missing	annual_physical	65	2026-10-12	3	\N
4359	4290	missing	annual_physical	65	2026-10-12	3	\N
4360	4291	missing	annual_physical	65	2026-10-12	3	\N
4361	4292	missing	annual_physical	65	2026-10-12	3	\N
4362	4293	missing	annual_physical	65	2026-10-12	3	\N
4363	4294	missing	annual_physical	65	2026-10-12	3	\N
4364	4295	missing	annual_physical	65	2026-10-12	3	\N
4365	4296	missing	annual_physical	65	2026-10-12	3	\N
4366	4297	missing	annual_physical	65	2026-10-12	3	\N
4367	4298	missing	annual_physical	65	2026-10-12	3	\N
4368	4299	missing	annual_physical	65	2026-10-12	3	\N
4369	4300	missing	annual_physical	65	2026-10-12	3	\N
4370	4301	missing	annual_physical	65	2026-10-12	3	\N
4371	4302	missing	annual_physical	65	2026-10-12	3	\N
4372	4303	missing	annual_physical	65	2026-10-12	3	\N
4373	4304	missing	annual_physical	65	2026-10-12	3	\N
4374	4305	missing	annual_physical	65	2026-10-12	3	\N
4375	4306	missing	annual_physical	65	2026-10-12	3	\N
4376	4307	missing	annual_physical	65	2026-10-12	3	\N
4377	4308	missing	annual_physical	65	2026-10-12	3	\N
4378	4309	missing	annual_physical	65	2026-10-12	3	\N
4379	4310	missing	annual_physical	65	2026-10-12	3	\N
4380	4311	missing	annual_physical	65	2026-10-12	3	\N
4381	4312	missing	annual_physical	65	2026-10-12	3	\N
4382	4313	missing	annual_physical	65	2026-10-12	3	\N
4383	4314	missing	annual_physical	65	2026-10-12	3	\N
4384	4315	missing	annual_physical	65	2026-10-12	3	\N
4385	4316	missing	annual_physical	65	2026-10-12	3	\N
4386	4317	missing	annual_physical	65	2026-10-12	3	\N
4387	4318	missing	annual_physical	65	2026-10-12	3	\N
4388	4319	missing	annual_physical	65	2026-10-12	3	\N
4389	4320	missing	annual_physical	65	2026-10-12	3	\N
4390	4321	missing	annual_physical	65	2026-10-12	3	\N
4391	4322	missing	annual_physical	65	2026-10-12	3	\N
4392	4323	missing	annual_physical	65	2026-10-12	3	\N
4393	4324	missing	annual_physical	65	2026-10-12	3	\N
4394	4325	missing	annual_physical	65	2026-10-12	3	\N
4395	4326	missing	annual_physical	65	2026-10-12	3	\N
4396	4327	missing	annual_physical	65	2026-10-12	3	\N
4397	4328	missing	annual_physical	65	2026-10-12	3	\N
4398	4329	missing	annual_physical	65	2026-10-12	3	\N
4399	4330	missing	annual_physical	65	2026-10-12	3	\N
4400	4331	missing	annual_physical	65	2026-10-12	3	\N
4401	4332	missing	annual_physical	65	2026-10-12	3	\N
4402	4333	missing	annual_physical	65	2026-10-12	3	\N
4403	4334	missing	annual_physical	65	2026-10-12	3	\N
4404	4335	missing	annual_physical	65	2026-10-12	3	\N
4405	4336	missing	annual_physical	65	2026-10-12	3	\N
4406	4337	missing	annual_physical	65	2026-10-12	3	\N
4407	4338	missing	annual_physical	65	2026-10-12	3	\N
4408	4339	missing	annual_physical	65	2026-10-12	3	\N
4409	4340	missing	annual_physical	65	2026-10-12	3	\N
4410	4341	missing	annual_physical	65	2026-10-12	3	\N
4411	4342	missing	annual_physical	65	2026-10-12	3	\N
4412	4343	missing	annual_physical	65	2026-10-12	3	\N
4413	4344	missing	annual_physical	65	2026-10-12	3	\N
4414	4345	missing	annual_physical	65	2026-10-12	3	\N
4415	4346	missing	annual_physical	65	2026-10-12	3	\N
4416	4347	missing	annual_physical	65	2026-10-12	3	\N
4417	4348	missing	annual_physical	65	2026-10-12	3	\N
4418	4349	missing	annual_physical	65	2026-10-12	3	\N
4419	4350	missing	annual_physical	65	2026-10-12	3	\N
4420	4351	missing	annual_physical	65	2026-10-12	3	\N
4421	4352	missing	annual_physical	65	2026-10-12	3	\N
4422	4353	missing	annual_physical	65	2026-10-12	3	\N
4423	4354	missing	annual_physical	65	2026-10-12	3	\N
4424	4355	missing	annual_physical	65	2026-10-12	3	\N
4425	4356	missing	annual_physical	65	2026-10-12	3	\N
4426	4357	missing	annual_physical	65	2026-10-12	3	\N
4427	4358	missing	annual_physical	65	2026-10-12	3	\N
4428	4359	missing	annual_physical	65	2026-10-12	3	\N
4429	4360	missing	annual_physical	65	2026-10-12	3	\N
4430	4361	missing	annual_physical	65	2026-10-12	3	\N
4431	4362	missing	annual_physical	65	2026-10-12	3	\N
4432	4363	missing	annual_physical	65	2026-10-12	3	\N
4433	4364	missing	annual_physical	65	2026-10-12	3	\N
4434	4365	missing	annual_physical	65	2026-10-12	3	\N
4435	4366	missing	annual_physical	65	2026-10-12	3	\N
4436	4367	missing	annual_physical	65	2026-10-12	3	\N
4437	4368	missing	annual_physical	65	2026-10-12	3	\N
4438	4369	missing	annual_physical	65	2026-10-12	3	\N
4439	4370	missing	annual_physical	65	2026-10-12	3	\N
4440	4371	missing	annual_physical	65	2026-10-12	3	\N
4441	4372	missing	annual_physical	65	2026-10-12	3	\N
4442	4373	missing	annual_physical	65	2026-10-12	3	\N
4443	4374	missing	annual_physical	65	2026-10-12	3	\N
4444	4375	missing	annual_physical	65	2026-10-12	3	\N
4445	4376	missing	annual_physical	65	2026-10-12	3	\N
4446	4377	missing	annual_physical	65	2026-10-12	3	\N
4447	4378	missing	annual_physical	65	2026-10-12	3	\N
4448	4379	missing	annual_physical	65	2026-10-12	3	\N
4449	4380	missing	annual_physical	65	2026-10-12	3	\N
4450	4381	missing	annual_physical	65	2026-10-12	3	\N
4451	4382	missing	annual_physical	65	2026-10-12	3	\N
4452	4383	missing	annual_physical	65	2026-10-12	3	\N
4453	4384	missing	annual_physical	65	2026-10-12	3	\N
4454	4385	missing	annual_physical	65	2026-10-12	3	\N
4455	4386	missing	annual_physical	65	2026-10-12	3	\N
4456	4387	missing	annual_physical	65	2026-10-12	3	\N
4457	4388	missing	annual_physical	65	2026-10-12	3	\N
4458	4389	missing	annual_physical	65	2026-10-12	3	\N
4459	4390	missing	annual_physical	65	2026-10-12	3	\N
4460	4391	missing	annual_physical	65	2026-10-12	3	\N
4461	4392	missing	annual_physical	65	2026-10-12	3	\N
4462	4393	missing	annual_physical	65	2026-10-12	3	\N
4463	4394	missing	annual_physical	65	2026-10-12	3	\N
4464	4395	missing	annual_physical	65	2026-10-12	3	\N
4465	4396	missing	annual_physical	65	2026-10-12	3	\N
4466	4397	missing	annual_physical	65	2026-10-12	3	\N
4467	4398	missing	annual_physical	65	2026-10-12	3	\N
4468	4399	missing	annual_physical	65	2026-10-12	3	\N
4469	4400	missing	annual_physical	65	2026-10-12	3	\N
4470	4401	missing	annual_physical	65	2026-10-12	3	\N
4471	4402	missing	annual_physical	65	2026-10-12	3	\N
4472	4403	missing	annual_physical	65	2026-10-12	3	\N
4473	4404	missing	annual_physical	65	2026-10-12	3	\N
4474	4405	missing	annual_physical	65	2026-10-12	3	\N
4475	4406	missing	annual_physical	65	2026-10-12	3	\N
4476	4407	missing	annual_physical	65	2026-10-12	3	\N
4477	4408	missing	annual_physical	65	2026-10-12	3	\N
4478	4409	missing	annual_physical	65	2026-10-12	3	\N
4479	4410	missing	annual_physical	65	2026-10-12	3	\N
4480	4411	missing	annual_physical	65	2026-10-12	3	\N
4481	4412	missing	annual_physical	65	2026-10-12	3	\N
4482	4413	missing	annual_physical	65	2026-10-12	3	\N
4483	4414	missing	annual_physical	65	2026-10-12	3	\N
4484	4415	missing	annual_physical	65	2026-10-12	3	\N
4485	4416	missing	annual_physical	65	2026-10-12	3	\N
4486	4417	missing	annual_physical	65	2026-10-12	3	\N
4487	4418	missing	annual_physical	65	2026-10-12	3	\N
4488	4419	missing	annual_physical	65	2026-10-12	3	\N
4489	4420	missing	annual_physical	65	2026-10-12	3	\N
4490	4421	missing	annual_physical	65	2026-10-12	3	\N
4491	4422	missing	annual_physical	65	2026-10-12	3	\N
4492	4423	missing	annual_physical	65	2026-10-12	3	\N
4493	4424	missing	annual_physical	65	2026-10-12	3	\N
4494	4425	missing	annual_physical	65	2026-10-12	3	\N
4495	4426	missing	annual_physical	65	2026-10-12	3	\N
4496	4427	missing	annual_physical	65	2026-10-12	3	\N
4497	4428	missing	annual_physical	65	2026-10-12	3	\N
4498	4429	missing	annual_physical	65	2026-10-12	3	\N
4499	4430	missing	annual_physical	65	2026-10-12	3	\N
4500	4431	missing	annual_physical	65	2026-10-12	3	\N
4501	4432	missing	annual_physical	65	2026-10-12	3	\N
4502	4433	missing	annual_physical	65	2026-10-12	3	\N
4503	4434	missing	annual_physical	65	2026-10-12	3	\N
4504	4435	missing	annual_physical	65	2026-10-12	3	\N
4505	4436	missing	annual_physical	65	2026-10-12	3	\N
4506	4437	missing	annual_physical	65	2026-10-12	3	\N
4507	4438	missing	annual_physical	65	2026-10-12	3	\N
4508	4439	missing	annual_physical	65	2026-10-12	3	\N
4509	4440	missing	annual_physical	65	2026-10-12	3	\N
4510	4441	missing	annual_physical	65	2026-10-12	3	\N
4511	4442	missing	annual_physical	65	2026-10-12	3	\N
4512	4443	missing	annual_physical	65	2026-10-12	3	\N
4513	4444	missing	annual_physical	65	2026-10-12	3	\N
4514	4445	missing	annual_physical	65	2026-10-12	3	\N
4515	4446	missing	annual_physical	65	2026-10-12	3	\N
4516	4447	missing	annual_physical	65	2026-10-12	3	\N
4517	4448	missing	annual_physical	65	2026-10-12	3	\N
4518	4449	missing	annual_physical	65	2026-10-12	3	\N
4519	4450	missing	annual_physical	65	2026-10-12	3	\N
4520	4451	missing	annual_physical	65	2026-10-12	3	\N
4521	4452	missing	annual_physical	65	2026-10-12	3	\N
4522	4453	missing	annual_physical	65	2026-10-12	3	\N
4523	4454	missing	annual_physical	65	2026-10-12	3	\N
4524	4455	missing	annual_physical	65	2026-10-12	3	\N
4525	4456	missing	annual_physical	65	2026-10-12	3	\N
4526	4457	missing	annual_physical	65	2026-10-12	3	\N
4527	4458	missing	annual_physical	65	2026-10-12	3	\N
4528	4459	missing	annual_physical	65	2026-10-12	3	\N
4529	4460	missing	annual_physical	65	2026-10-12	3	\N
4530	4461	missing	annual_physical	65	2026-10-12	3	\N
4531	4462	missing	annual_physical	65	2026-10-12	3	\N
4532	4463	missing	annual_physical	65	2026-10-12	3	\N
4533	4464	missing	annual_physical	65	2026-10-12	3	\N
4534	4465	missing	annual_physical	65	2026-10-12	3	\N
4535	4466	missing	annual_physical	65	2026-10-12	3	\N
4536	4467	missing	annual_physical	65	2026-10-12	3	\N
4537	4468	missing	annual_physical	65	2026-10-12	3	\N
4538	4469	missing	annual_physical	65	2026-10-12	3	\N
4539	4470	missing	annual_physical	65	2026-10-12	3	\N
4540	4471	missing	annual_physical	65	2026-10-12	3	\N
4541	4472	missing	annual_physical	65	2026-10-12	3	\N
4542	4473	missing	annual_physical	65	2026-10-12	3	\N
4543	4474	missing	annual_physical	65	2026-10-12	3	\N
4544	4475	missing	annual_physical	65	2026-10-12	3	\N
4545	4476	missing	annual_physical	65	2026-10-12	3	\N
4546	4477	missing	annual_physical	65	2026-10-12	3	\N
4547	4478	missing	annual_physical	65	2026-10-12	3	\N
4548	4479	missing	annual_physical	65	2026-10-12	3	\N
4549	4480	missing	annual_physical	65	2026-10-12	3	\N
4550	4481	missing	annual_physical	65	2026-10-12	3	\N
4551	4482	missing	annual_physical	65	2026-10-12	3	\N
4552	4483	missing	annual_physical	65	2026-10-12	3	\N
4553	4484	missing	annual_physical	65	2026-10-12	3	\N
4554	4485	missing	annual_physical	65	2026-10-12	3	\N
4555	4486	missing	annual_physical	65	2026-10-12	3	\N
4556	4487	missing	annual_physical	65	2026-10-12	3	\N
4557	4488	missing	annual_physical	65	2026-10-12	3	\N
4558	4489	missing	annual_physical	65	2026-10-12	3	\N
4559	4490	missing	annual_physical	65	2026-10-12	3	\N
4560	4491	missing	annual_physical	65	2026-10-12	3	\N
4561	4492	missing	annual_physical	65	2026-10-12	3	\N
4562	4493	missing	annual_physical	65	2026-10-12	3	\N
4563	4494	missing	annual_physical	65	2026-10-12	3	\N
4564	4495	missing	annual_physical	65	2026-10-12	3	\N
4565	4496	missing	annual_physical	65	2026-10-12	3	\N
4566	4497	missing	annual_physical	65	2026-10-12	3	\N
4567	4498	missing	annual_physical	65	2026-10-12	3	\N
4568	4499	missing	annual_physical	65	2026-10-12	3	\N
4569	4500	missing	annual_physical	65	2026-10-12	3	\N
4570	4501	missing	annual_physical	65	2026-10-12	3	\N
4571	4502	missing	annual_physical	65	2026-10-12	3	\N
4572	4503	missing	annual_physical	65	2026-10-12	3	\N
4573	4504	missing	annual_physical	65	2026-10-12	3	\N
4574	4505	missing	annual_physical	65	2026-10-12	3	\N
4575	4506	missing	annual_physical	65	2026-10-12	3	\N
4576	4507	missing	annual_physical	65	2026-10-12	3	\N
4577	4508	missing	annual_physical	65	2026-10-12	3	\N
4578	4509	missing	annual_physical	65	2026-10-12	3	\N
4579	4510	missing	annual_physical	65	2026-10-12	3	\N
4580	4511	missing	annual_physical	65	2026-10-12	3	\N
4581	4512	borrowed	annual_physical	65	2026-10-12	3	\N
4582	4513	missing	annual_physical	65	2026-10-12	3	\N
4583	4514	missing	annual_physical	65	2026-10-12	3	\N
4584	4515	missing	annual_physical	65	2026-10-12	3	\N
4585	4516	missing	annual_physical	65	2026-10-12	3	\N
4586	4517	missing	annual_physical	65	2026-10-12	3	\N
4587	4518	missing	annual_physical	65	2026-10-12	3	\N
4588	4519	missing	annual_physical	65	2026-10-12	3	\N
4589	4520	missing	annual_physical	65	2026-10-12	3	\N
4590	4521	missing	annual_physical	65	2026-10-12	3	\N
4591	4522	missing	annual_physical	65	2026-10-12	3	\N
4592	4523	missing	annual_physical	65	2026-10-12	3	\N
4593	4524	missing	annual_physical	65	2026-10-12	3	\N
4594	4525	missing	annual_physical	65	2026-10-12	3	\N
4595	4526	missing	annual_physical	65	2026-10-12	3	\N
4596	4527	missing	annual_physical	65	2026-10-12	3	\N
4597	4528	missing	annual_physical	65	2026-10-12	3	\N
4598	4529	missing	annual_physical	65	2026-10-12	3	\N
4599	4530	missing	annual_physical	65	2026-10-12	3	\N
4600	4531	missing	annual_physical	65	2026-10-12	3	\N
4601	4532	missing	annual_physical	65	2026-10-12	3	\N
4602	4533	missing	annual_physical	65	2026-10-12	3	\N
4603	4534	missing	annual_physical	65	2026-10-12	3	\N
4604	4535	missing	annual_physical	65	2026-10-12	3	\N
4605	4536	missing	annual_physical	65	2026-10-12	3	\N
4606	4537	missing	annual_physical	65	2026-10-12	3	\N
4607	4538	missing	annual_physical	65	2026-10-12	3	\N
4608	4539	missing	annual_physical	65	2026-10-12	3	\N
4609	4540	missing	annual_physical	65	2026-10-12	3	\N
4610	4541	missing	annual_physical	65	2026-10-12	3	\N
4611	4542	missing	annual_physical	65	2026-10-12	3	\N
4612	4543	missing	annual_physical	65	2026-10-12	3	\N
4613	4544	missing	annual_physical	65	2026-10-12	3	\N
4614	4545	missing	annual_physical	65	2026-10-12	3	\N
4615	4546	missing	annual_physical	65	2026-10-12	3	\N
4616	4547	missing	annual_physical	65	2026-10-12	3	\N
4617	4548	missing	annual_physical	65	2026-10-12	3	\N
4618	4549	missing	annual_physical	65	2026-10-12	3	\N
4619	4550	missing	annual_physical	65	2026-10-12	3	\N
4620	4551	missing	annual_physical	65	2026-10-12	3	\N
4621	4552	missing	annual_physical	65	2026-10-12	3	\N
4622	4553	missing	annual_physical	65	2026-10-12	3	\N
4623	4554	missing	annual_physical	65	2026-10-12	3	\N
4624	4555	missing	annual_physical	65	2026-10-12	3	\N
4625	4556	missing	annual_physical	65	2026-10-12	3	\N
4626	4557	missing	annual_physical	65	2026-10-12	3	\N
4627	4558	missing	annual_physical	65	2026-10-12	3	\N
4628	4559	missing	annual_physical	65	2026-10-12	3	\N
4629	4560	missing	annual_physical	65	2026-10-12	3	\N
4630	4561	missing	annual_physical	65	2026-10-12	3	\N
4631	4562	missing	annual_physical	65	2026-10-12	3	\N
4632	4563	missing	annual_physical	65	2026-10-12	3	\N
4633	4564	missing	annual_physical	65	2026-10-12	3	\N
4634	4565	missing	annual_physical	65	2026-10-12	3	\N
4635	4566	missing	annual_physical	65	2026-10-12	3	\N
4636	4567	missing	annual_physical	65	2026-10-12	3	\N
4637	4568	missing	annual_physical	65	2026-10-12	3	\N
4638	4569	missing	annual_physical	65	2026-10-12	3	\N
4639	4570	missing	annual_physical	65	2026-10-12	3	\N
4640	4571	missing	annual_physical	65	2026-10-12	3	\N
4641	4572	missing	annual_physical	65	2026-10-12	3	\N
4642	4573	missing	annual_physical	65	2026-10-12	3	\N
4643	4574	missing	annual_physical	65	2026-10-12	3	\N
4644	4575	missing	annual_physical	65	2026-10-12	3	\N
4645	4576	missing	annual_physical	65	2026-10-12	3	\N
4646	4577	missing	annual_physical	65	2026-10-12	3	\N
4647	4578	missing	annual_physical	65	2026-10-12	3	\N
4648	4579	missing	annual_physical	65	2026-10-12	3	\N
4649	4580	missing	annual_physical	65	2026-10-12	3	\N
4650	4581	missing	annual_physical	65	2026-10-12	3	\N
4651	4582	missing	annual_physical	65	2026-10-12	3	\N
4652	4583	missing	annual_physical	65	2026-10-12	3	\N
4653	4584	missing	annual_physical	65	2026-10-12	3	\N
4654	4585	missing	annual_physical	65	2026-10-12	3	\N
4655	4586	missing	annual_physical	65	2026-10-12	3	\N
4656	4587	missing	annual_physical	65	2026-10-12	3	\N
4657	4588	missing	annual_physical	65	2026-10-12	3	\N
4658	4589	missing	annual_physical	65	2026-10-12	3	\N
4659	4590	missing	annual_physical	65	2026-10-12	3	\N
4660	4591	missing	annual_physical	65	2026-10-12	3	\N
4661	4592	missing	annual_physical	65	2026-10-12	3	\N
4662	4593	missing	annual_physical	65	2026-10-12	3	\N
4663	4594	missing	annual_physical	65	2026-10-12	3	\N
4664	4595	missing	annual_physical	65	2026-10-12	3	\N
4665	4596	missing	annual_physical	65	2026-10-12	3	\N
4666	4597	missing	annual_physical	65	2026-10-12	3	\N
4667	4598	missing	annual_physical	65	2026-10-12	3	\N
4668	4599	missing	annual_physical	65	2026-10-12	3	\N
4669	4600	missing	annual_physical	65	2026-10-12	3	\N
4670	4601	missing	annual_physical	65	2026-10-12	3	\N
4671	4602	missing	annual_physical	65	2026-10-12	3	\N
4672	4603	missing	annual_physical	65	2026-10-12	3	\N
4673	4604	missing	annual_physical	65	2026-10-12	3	\N
4674	4605	missing	annual_physical	65	2026-10-12	3	\N
4675	4606	missing	annual_physical	65	2026-10-12	3	\N
4676	4607	missing	annual_physical	65	2026-10-12	3	\N
4677	4608	missing	annual_physical	65	2026-10-12	3	\N
4678	4609	missing	annual_physical	65	2026-10-12	3	\N
4679	4610	missing	annual_physical	65	2026-10-12	3	\N
4680	4611	missing	annual_physical	65	2026-10-12	3	\N
4681	4612	missing	annual_physical	65	2026-10-12	3	\N
4682	4613	missing	annual_physical	65	2026-10-12	3	\N
4683	4614	missing	annual_physical	65	2026-10-12	3	\N
4684	4615	missing	annual_physical	65	2026-10-12	3	\N
4685	4616	missing	annual_physical	65	2026-10-12	3	\N
4686	4617	missing	annual_physical	65	2026-10-12	3	\N
4687	4618	missing	annual_physical	65	2026-10-12	3	\N
4688	4619	missing	annual_physical	65	2026-10-12	3	\N
4689	4620	missing	annual_physical	65	2026-10-12	3	\N
4690	4621	missing	annual_physical	65	2026-10-12	3	\N
4691	4622	missing	annual_physical	65	2026-10-12	3	\N
4692	4623	missing	annual_physical	65	2026-10-12	3	\N
4693	4624	missing	annual_physical	65	2026-10-12	3	\N
4694	4625	missing	annual_physical	65	2026-10-12	3	\N
4695	4626	missing	annual_physical	65	2026-10-12	3	\N
4696	4627	missing	annual_physical	65	2026-10-12	3	\N
4697	4628	missing	annual_physical	65	2026-10-12	3	\N
4698	4629	missing	annual_physical	65	2026-10-12	3	\N
4699	4630	missing	annual_physical	65	2026-10-12	3	\N
4700	4631	missing	annual_physical	65	2026-10-12	3	\N
4701	4632	missing	annual_physical	65	2026-10-12	3	\N
4702	4633	missing	annual_physical	65	2026-10-12	3	\N
4703	4634	missing	annual_physical	65	2026-10-12	3	\N
4704	4635	missing	annual_physical	65	2026-10-12	3	\N
4705	4636	missing	annual_physical	65	2026-10-12	3	\N
4706	4637	missing	annual_physical	65	2026-10-12	3	\N
4707	4638	missing	annual_physical	65	2026-10-12	3	\N
4708	4639	missing	annual_physical	65	2026-10-12	3	\N
4709	4640	missing	annual_physical	65	2026-10-12	3	\N
4710	4641	missing	annual_physical	65	2026-10-12	3	\N
4711	4642	missing	annual_physical	65	2026-10-12	3	\N
4712	4643	missing	annual_physical	65	2026-10-12	3	\N
4713	4644	missing	annual_physical	65	2026-10-12	3	\N
4714	4645	missing	annual_physical	65	2026-10-12	3	\N
4715	4646	missing	annual_physical	65	2026-10-12	3	\N
4716	4647	missing	annual_physical	65	2026-10-12	3	\N
4717	4648	missing	annual_physical	65	2026-10-12	3	\N
4718	4649	missing	annual_physical	65	2026-10-12	3	\N
4719	4650	missing	annual_physical	65	2026-10-12	3	\N
4720	4651	missing	annual_physical	65	2026-10-12	3	\N
4721	4652	missing	annual_physical	65	2026-10-12	3	\N
4722	4653	missing	annual_physical	65	2026-10-12	3	\N
4723	4654	missing	annual_physical	65	2026-10-12	3	\N
4724	4655	missing	annual_physical	65	2026-10-12	3	\N
4725	4656	missing	annual_physical	65	2026-10-12	3	\N
4726	4657	missing	annual_physical	65	2026-10-12	3	\N
4727	4658	missing	annual_physical	65	2026-10-12	3	\N
4728	4659	missing	annual_physical	65	2026-10-12	3	\N
4729	4660	missing	annual_physical	65	2026-10-12	3	\N
4730	4661	missing	annual_physical	65	2026-10-12	3	\N
4731	4662	missing	annual_physical	65	2026-10-12	3	\N
4732	4663	missing	annual_physical	65	2026-10-12	3	\N
4733	4664	missing	annual_physical	65	2026-10-12	3	\N
4734	4665	missing	annual_physical	65	2026-10-12	3	\N
4735	4666	missing	annual_physical	65	2026-10-12	3	\N
4736	4667	missing	annual_physical	65	2026-10-12	3	\N
4737	4668	missing	annual_physical	65	2026-10-12	3	\N
4738	4669	missing	annual_physical	65	2026-10-12	3	\N
4739	4670	missing	annual_physical	65	2026-10-12	3	\N
4740	4671	missing	annual_physical	65	2026-10-12	3	\N
4741	4672	missing	annual_physical	65	2026-10-12	3	\N
4742	4673	missing	annual_physical	65	2026-10-12	3	\N
4743	4674	missing	annual_physical	65	2026-10-12	3	\N
4744	4675	missing	annual_physical	65	2026-10-12	3	\N
4745	4676	missing	annual_physical	65	2026-10-12	3	\N
4746	4677	missing	annual_physical	65	2026-10-12	3	\N
4747	4678	missing	annual_physical	65	2026-10-12	3	\N
4748	4679	missing	annual_physical	65	2026-10-12	3	\N
4749	4680	missing	annual_physical	65	2026-10-12	3	\N
4750	4681	missing	annual_physical	65	2026-10-12	3	\N
4751	4682	missing	annual_physical	65	2026-10-12	3	\N
4752	4683	missing	annual_physical	65	2026-10-12	3	\N
4753	4684	missing	annual_physical	65	2026-10-12	3	\N
4754	4685	missing	annual_physical	65	2026-10-12	3	\N
4755	4686	missing	annual_physical	65	2026-10-12	3	\N
4756	4687	missing	annual_physical	65	2026-10-12	3	\N
4757	4688	missing	annual_physical	65	2026-10-12	3	\N
4758	4689	missing	annual_physical	65	2026-10-12	3	\N
4759	4690	missing	annual_physical	65	2026-10-12	3	\N
4760	4691	missing	annual_physical	65	2026-10-12	3	\N
4761	4692	missing	annual_physical	65	2026-10-12	3	\N
4762	4693	missing	annual_physical	65	2026-10-12	3	\N
4763	4694	missing	annual_physical	65	2026-10-12	3	\N
4764	4695	missing	annual_physical	65	2026-10-12	3	\N
4765	4696	missing	annual_physical	65	2026-10-12	3	\N
4766	4697	missing	annual_physical	65	2026-10-12	3	\N
4767	4698	missing	annual_physical	65	2026-10-12	3	\N
4768	4699	missing	annual_physical	65	2026-10-12	3	\N
4769	4700	missing	annual_physical	65	2026-10-12	3	\N
4770	4701	missing	annual_physical	65	2026-10-12	3	\N
4771	4702	missing	annual_physical	65	2026-10-12	3	\N
4772	4703	missing	annual_physical	65	2026-10-12	3	\N
4773	4704	missing	annual_physical	65	2026-10-12	3	\N
4774	4705	missing	annual_physical	65	2026-10-12	3	\N
4775	4706	missing	annual_physical	65	2026-10-12	3	\N
4776	4707	missing	annual_physical	65	2026-10-12	3	\N
4777	4708	missing	annual_physical	65	2026-10-12	3	\N
4778	4709	missing	annual_physical	65	2026-10-12	3	\N
4779	4710	missing	annual_physical	65	2026-10-12	3	\N
4780	4711	missing	annual_physical	65	2026-10-12	3	\N
4781	4712	missing	annual_physical	65	2026-10-12	3	\N
4782	4713	missing	annual_physical	65	2026-10-12	3	\N
4783	4714	missing	annual_physical	65	2026-10-12	3	\N
4784	4715	missing	annual_physical	65	2026-10-12	3	\N
4785	4716	missing	annual_physical	65	2026-10-12	3	\N
4786	4717	missing	annual_physical	65	2026-10-12	3	\N
4787	4718	missing	annual_physical	65	2026-10-12	3	\N
4788	4719	missing	annual_physical	65	2026-10-12	3	\N
4789	4720	missing	annual_physical	65	2026-10-12	3	\N
4790	4721	missing	annual_physical	65	2026-10-12	3	\N
4791	4722	missing	annual_physical	65	2026-10-12	3	\N
4792	4723	missing	annual_physical	65	2026-10-12	3	\N
4793	4724	missing	annual_physical	65	2026-10-12	3	\N
4794	4725	missing	annual_physical	65	2026-10-12	3	\N
4795	4726	missing	annual_physical	65	2026-10-12	3	\N
4796	4727	missing	annual_physical	65	2026-10-12	3	\N
4797	4728	missing	annual_physical	65	2026-10-12	3	\N
4798	4729	borrowed	annual_physical	65	2026-10-12	3	\N
4799	4730	missing	annual_physical	65	2026-10-12	3	\N
4800	4731	missing	annual_physical	65	2026-10-12	3	\N
4801	4732	missing	annual_physical	65	2026-10-12	3	\N
4802	4733	missing	annual_physical	65	2026-10-12	3	\N
4803	4734	missing	annual_physical	65	2026-10-12	3	\N
4804	4735	missing	annual_physical	65	2026-10-12	3	\N
4805	4736	missing	annual_physical	65	2026-10-12	3	\N
4806	4737	missing	annual_physical	65	2026-10-12	3	\N
4807	4738	missing	annual_physical	65	2026-10-12	3	\N
4808	4739	missing	annual_physical	65	2026-10-12	3	\N
4809	4740	missing	annual_physical	65	2026-10-12	3	\N
4810	4741	missing	annual_physical	65	2026-10-12	3	\N
4811	4742	missing	annual_physical	65	2026-10-12	3	\N
4812	4743	missing	annual_physical	65	2026-10-12	3	\N
4813	4744	missing	annual_physical	65	2026-10-12	3	\N
4814	4745	missing	annual_physical	65	2026-10-12	3	\N
4815	4746	missing	annual_physical	65	2026-10-12	3	\N
4816	4747	missing	annual_physical	65	2026-10-12	3	\N
4817	4748	missing	annual_physical	65	2026-10-12	3	\N
4818	4749	missing	annual_physical	65	2026-10-12	3	\N
4819	4750	missing	annual_physical	65	2026-10-12	3	\N
4820	4751	missing	annual_physical	65	2026-10-12	3	\N
4821	4752	missing	annual_physical	65	2026-10-12	3	\N
4822	4753	missing	annual_physical	65	2026-10-12	3	\N
4823	4754	missing	annual_physical	65	2026-10-12	3	\N
4824	4755	missing	annual_physical	65	2026-10-12	3	\N
4825	4756	missing	annual_physical	65	2026-10-12	3	\N
4826	4757	missing	annual_physical	65	2026-10-12	3	\N
4827	4758	missing	annual_physical	65	2026-10-12	3	\N
4828	4759	missing	annual_physical	65	2026-10-12	3	\N
4829	4760	missing	annual_physical	65	2026-10-12	3	\N
4830	4761	missing	annual_physical	65	2026-10-12	3	\N
4831	4762	missing	annual_physical	65	2026-10-12	3	\N
4832	4763	missing	annual_physical	65	2026-10-12	3	\N
4833	4764	missing	annual_physical	65	2026-10-12	3	\N
4834	4765	missing	annual_physical	65	2026-10-12	3	\N
4835	4766	missing	annual_physical	65	2026-10-12	3	\N
4836	4767	missing	annual_physical	65	2026-10-12	3	\N
4837	4768	missing	annual_physical	65	2026-10-12	3	\N
4838	4769	missing	annual_physical	65	2026-10-12	3	\N
4839	4770	missing	annual_physical	65	2026-10-12	3	\N
4840	4771	missing	annual_physical	65	2026-10-12	3	\N
4841	4772	missing	annual_physical	65	2026-10-12	3	\N
4842	4773	missing	annual_physical	65	2026-10-12	3	\N
4843	4774	missing	annual_physical	65	2026-10-12	3	\N
4844	4775	missing	annual_physical	65	2026-10-12	3	\N
4845	4776	missing	annual_physical	65	2026-10-12	3	\N
4846	4777	missing	annual_physical	65	2026-10-12	3	\N
4847	4778	missing	annual_physical	65	2026-10-12	3	\N
4848	4779	missing	annual_physical	65	2026-10-12	3	\N
4849	4780	missing	annual_physical	65	2026-10-12	3	\N
4850	4781	missing	annual_physical	65	2026-10-12	3	\N
4851	4782	missing	annual_physical	65	2026-10-12	3	\N
4852	4783	missing	annual_physical	65	2026-10-12	3	\N
4853	4784	missing	annual_physical	65	2026-10-12	3	\N
4854	4785	missing	annual_physical	65	2026-10-12	3	\N
4855	4786	missing	annual_physical	65	2026-10-12	3	\N
4856	4787	missing	annual_physical	65	2026-10-12	3	\N
4857	4788	missing	annual_physical	65	2026-10-12	3	\N
4858	4789	missing	annual_physical	65	2026-10-12	3	\N
4859	4790	missing	annual_physical	65	2026-10-12	3	\N
4860	4791	missing	annual_physical	65	2026-10-12	3	\N
4861	4792	missing	annual_physical	65	2026-10-12	3	\N
4862	4793	missing	annual_physical	65	2026-10-12	3	\N
4863	4794	missing	annual_physical	65	2026-10-12	3	\N
4864	4795	missing	annual_physical	65	2026-10-12	3	\N
4865	4796	missing	annual_physical	65	2026-10-12	3	\N
4866	4797	missing	annual_physical	65	2026-10-12	3	\N
4867	4798	missing	annual_physical	65	2026-10-12	3	\N
4868	4799	missing	annual_physical	65	2026-10-12	3	\N
4869	4800	missing	annual_physical	65	2026-10-12	3	\N
4870	4801	missing	annual_physical	65	2026-10-12	3	\N
4871	4802	missing	annual_physical	65	2026-10-12	3	\N
4872	4803	missing	annual_physical	65	2026-10-12	3	\N
4873	4804	missing	annual_physical	65	2026-10-12	3	\N
4874	4805	missing	annual_physical	65	2026-10-12	3	\N
4875	4806	missing	annual_physical	65	2026-10-12	3	\N
4876	4807	missing	annual_physical	65	2026-10-12	3	\N
4877	4808	missing	annual_physical	65	2026-10-12	3	\N
4878	4809	missing	annual_physical	65	2026-10-12	3	\N
4879	4810	missing	annual_physical	65	2026-10-12	3	\N
4880	4811	missing	annual_physical	65	2026-10-12	3	\N
4881	4812	missing	annual_physical	65	2026-10-12	3	\N
4882	4813	missing	annual_physical	65	2026-10-12	3	\N
4883	4814	missing	annual_physical	65	2026-10-12	3	\N
4884	4815	missing	annual_physical	65	2026-10-12	3	\N
4885	4816	missing	annual_physical	65	2026-10-12	3	\N
4886	4817	missing	annual_physical	65	2026-10-12	3	\N
4887	4818	missing	annual_physical	65	2026-10-12	3	\N
4888	4819	missing	annual_physical	65	2026-10-12	3	\N
4889	4820	missing	annual_physical	65	2026-10-12	3	\N
4890	4821	missing	annual_physical	65	2026-10-12	3	\N
4891	4822	missing	annual_physical	65	2026-10-12	3	\N
4892	4823	missing	annual_physical	65	2026-10-12	3	\N
4893	4824	missing	annual_physical	65	2026-10-12	3	\N
4894	4825	missing	annual_physical	65	2026-10-12	3	\N
4895	4826	missing	annual_physical	65	2026-10-12	3	\N
4896	4827	missing	annual_physical	65	2026-10-12	3	\N
4897	4828	missing	annual_physical	65	2026-10-12	3	\N
4898	4829	missing	annual_physical	65	2026-10-12	3	\N
4899	4830	missing	annual_physical	65	2026-10-12	3	\N
4900	4831	missing	annual_physical	65	2026-10-12	3	\N
4901	4832	missing	annual_physical	65	2026-10-12	3	\N
4902	4833	missing	annual_physical	65	2026-10-12	3	\N
4903	4834	missing	annual_physical	65	2026-10-12	3	\N
4904	4835	missing	annual_physical	65	2026-10-12	3	\N
4905	4836	missing	annual_physical	65	2026-10-12	3	\N
4906	4837	missing	annual_physical	65	2026-10-12	3	\N
4907	4838	missing	annual_physical	65	2026-10-12	3	\N
4908	4839	missing	annual_physical	65	2026-10-12	3	\N
4909	4840	missing	annual_physical	65	2026-10-12	3	\N
4910	4841	missing	annual_physical	65	2026-10-12	3	\N
4911	4842	missing	annual_physical	65	2026-10-12	3	\N
4912	4843	missing	annual_physical	65	2026-10-12	3	\N
4913	4844	missing	annual_physical	65	2026-10-12	3	\N
4914	4845	missing	annual_physical	65	2026-10-12	3	\N
4915	4846	missing	annual_physical	65	2026-10-12	3	\N
4916	4847	missing	annual_physical	65	2026-10-12	3	\N
4917	4848	missing	annual_physical	65	2026-10-12	3	\N
4918	4849	missing	annual_physical	65	2026-10-12	3	\N
4919	4850	missing	annual_physical	65	2026-10-12	3	\N
4920	4851	missing	annual_physical	65	2026-10-12	3	\N
4921	4852	missing	annual_physical	65	2026-10-12	3	\N
4922	4853	missing	annual_physical	65	2026-10-12	3	\N
4923	4854	missing	annual_physical	65	2026-10-12	3	\N
4924	4855	missing	annual_physical	65	2026-10-12	3	\N
4925	4856	missing	annual_physical	65	2026-10-12	3	\N
4926	4857	missing	annual_physical	65	2026-10-12	3	\N
4927	4858	missing	annual_physical	65	2026-10-12	3	\N
4928	4859	missing	annual_physical	65	2026-10-12	3	\N
4929	4860	missing	annual_physical	65	2026-10-12	3	\N
4930	4861	missing	annual_physical	65	2026-10-12	3	\N
4931	4862	missing	annual_physical	65	2026-10-12	3	\N
4932	4863	missing	annual_physical	65	2026-10-12	3	\N
4933	4864	missing	annual_physical	65	2026-10-12	3	\N
4934	4865	missing	annual_physical	65	2026-10-12	3	\N
4935	4866	missing	annual_physical	65	2026-10-12	3	\N
4936	4867	missing	annual_physical	65	2026-10-12	3	\N
4937	4868	missing	annual_physical	65	2026-10-12	3	\N
4938	4869	missing	annual_physical	65	2026-10-12	3	\N
4939	4870	missing	annual_physical	65	2026-10-12	3	\N
4940	4871	missing	annual_physical	65	2026-10-12	3	\N
4941	4872	missing	annual_physical	65	2026-10-12	3	\N
4942	4873	missing	annual_physical	65	2026-10-12	3	\N
4943	4874	missing	annual_physical	65	2026-10-12	3	\N
4944	4875	missing	annual_physical	65	2026-10-12	3	\N
4945	4876	missing	annual_physical	65	2026-10-12	3	\N
4946	4877	missing	annual_physical	65	2026-10-12	3	\N
4947	4878	missing	annual_physical	65	2026-10-12	3	\N
4948	4879	missing	annual_physical	65	2026-10-12	3	\N
4949	4880	missing	annual_physical	65	2026-10-12	3	\N
4950	4881	missing	annual_physical	65	2026-10-12	3	\N
4951	4882	missing	annual_physical	65	2026-10-12	3	\N
4952	4883	missing	annual_physical	65	2026-10-12	3	\N
4953	4884	missing	annual_physical	65	2026-10-12	3	\N
4954	4885	missing	annual_physical	65	2026-10-12	3	\N
4955	4886	missing	annual_physical	65	2026-10-12	3	\N
4956	4887	missing	annual_physical	65	2026-10-12	3	\N
4957	4888	missing	annual_physical	65	2026-10-12	3	\N
4958	4889	missing	annual_physical	65	2026-10-12	3	\N
4959	4890	missing	annual_physical	65	2026-10-12	3	\N
4960	4891	missing	annual_physical	65	2026-10-12	3	\N
4961	4892	missing	annual_physical	65	2026-10-12	3	\N
4962	4893	missing	annual_physical	65	2026-10-12	3	\N
4963	4894	missing	annual_physical	65	2026-10-12	3	\N
4964	4895	missing	annual_physical	65	2026-10-12	3	\N
4965	4896	missing	annual_physical	65	2026-10-12	3	\N
4966	4897	missing	annual_physical	65	2026-10-12	3	\N
4967	4898	missing	annual_physical	65	2026-10-12	3	\N
4968	4899	missing	annual_physical	65	2026-10-12	3	\N
4969	4900	missing	annual_physical	65	2026-10-12	3	\N
4970	4901	missing	annual_physical	65	2026-10-12	3	\N
4971	4902	missing	annual_physical	65	2026-10-12	3	\N
4972	4903	missing	annual_physical	65	2026-10-12	3	\N
4973	4904	missing	annual_physical	65	2026-10-12	3	\N
4974	4905	missing	annual_physical	65	2026-10-12	3	\N
4975	4906	missing	annual_physical	65	2026-10-12	3	\N
4976	4907	missing	annual_physical	65	2026-10-12	3	\N
4977	4908	missing	annual_physical	65	2026-10-12	3	\N
4978	4909	missing	annual_physical	65	2026-10-12	3	\N
4979	4910	missing	annual_physical	65	2026-10-12	3	\N
4980	4911	missing	annual_physical	65	2026-10-12	3	\N
4981	4912	missing	annual_physical	65	2026-10-12	3	\N
4982	4913	missing	annual_physical	65	2026-10-12	3	\N
4983	4914	missing	annual_physical	65	2026-10-12	3	\N
4984	4915	missing	annual_physical	65	2026-10-12	3	\N
4985	4916	missing	annual_physical	65	2026-10-12	3	\N
4986	4917	missing	annual_physical	65	2026-10-12	3	\N
4987	4918	missing	annual_physical	65	2026-10-12	3	\N
4988	4919	missing	annual_physical	65	2026-10-12	3	\N
4989	4920	missing	annual_physical	65	2026-10-12	3	\N
4990	4921	missing	annual_physical	65	2026-10-12	3	\N
4991	4922	missing	annual_physical	65	2026-10-12	3	\N
4992	4923	missing	annual_physical	65	2026-10-12	3	\N
4993	4924	missing	annual_physical	65	2026-10-12	3	\N
4994	4925	missing	annual_physical	65	2026-10-12	3	\N
4995	4926	missing	annual_physical	65	2026-10-12	3	\N
4996	4927	missing	annual_physical	65	2026-10-12	3	\N
4997	4928	missing	annual_physical	65	2026-10-12	3	\N
4998	4929	missing	annual_physical	65	2026-10-12	3	\N
4999	4930	missing	annual_physical	65	2026-10-12	3	\N
5000	4931	missing	annual_physical	65	2026-10-12	3	\N
5001	4932	missing	annual_physical	65	2026-10-12	3	\N
5002	4933	missing	annual_physical	65	2026-10-12	3	\N
5003	4934	missing	annual_physical	65	2026-10-12	3	\N
5004	4935	missing	annual_physical	65	2026-10-12	3	\N
5005	4936	missing	annual_physical	65	2026-10-12	3	\N
5006	4937	missing	annual_physical	65	2026-10-12	3	\N
5007	4938	missing	annual_physical	65	2026-10-12	3	\N
5008	4939	missing	annual_physical	65	2026-10-12	3	\N
5009	4940	missing	annual_physical	65	2026-10-12	3	\N
5010	4941	missing	annual_physical	65	2026-10-12	3	\N
5011	4942	missing	annual_physical	65	2026-10-12	3	\N
5012	4943	missing	annual_physical	65	2026-10-12	3	\N
5013	4944	missing	annual_physical	65	2026-10-12	3	\N
5014	4945	missing	annual_physical	65	2026-10-12	3	\N
5015	4946	missing	annual_physical	65	2026-10-12	3	\N
5016	4947	missing	annual_physical	65	2026-10-12	3	\N
5017	4948	missing	annual_physical	65	2026-10-12	3	\N
5018	4949	missing	annual_physical	65	2026-10-12	3	\N
5019	4950	missing	annual_physical	65	2026-10-12	3	\N
5020	4951	missing	annual_physical	65	2026-10-12	3	\N
5021	4952	missing	annual_physical	65	2026-10-12	3	\N
5022	4953	missing	annual_physical	65	2026-10-12	3	\N
5023	4954	missing	annual_physical	65	2026-10-12	3	\N
5024	4955	missing	annual_physical	65	2026-10-12	3	\N
5025	4956	missing	annual_physical	65	2026-10-12	3	\N
5026	4957	missing	annual_physical	65	2026-10-12	3	\N
5027	4958	missing	annual_physical	65	2026-10-12	3	\N
5028	4959	missing	annual_physical	65	2026-10-12	3	\N
5029	4960	missing	annual_physical	65	2026-10-12	3	\N
5030	4961	missing	annual_physical	65	2026-10-12	3	\N
5031	4962	missing	annual_physical	65	2026-10-12	3	\N
5032	4963	missing	annual_physical	65	2026-10-12	3	\N
5033	4964	missing	annual_physical	65	2026-10-12	3	\N
5034	4965	missing	annual_physical	65	2026-10-12	3	\N
5035	4966	missing	annual_physical	65	2026-10-12	3	\N
5036	4967	missing	annual_physical	65	2026-10-12	3	\N
5037	4968	missing	annual_physical	65	2026-10-12	3	\N
5038	4969	missing	annual_physical	65	2026-10-12	3	\N
5039	4970	missing	annual_physical	65	2026-10-12	3	\N
5040	4971	missing	annual_physical	65	2026-10-12	3	\N
5041	4972	missing	annual_physical	65	2026-10-12	3	\N
5042	4973	missing	annual_physical	65	2026-10-12	3	\N
5043	4974	missing	annual_physical	65	2026-10-12	3	\N
5044	4975	missing	annual_physical	65	2026-10-12	3	\N
5045	4976	missing	annual_physical	65	2026-10-12	3	\N
5046	4977	missing	annual_physical	65	2026-10-12	3	\N
5047	4978	missing	annual_physical	65	2026-10-12	3	\N
5048	4979	missing	annual_physical	65	2026-10-12	3	\N
5049	4980	missing	annual_physical	65	2026-10-12	3	\N
5050	4981	missing	annual_physical	65	2026-10-12	3	\N
5051	4982	missing	annual_physical	65	2026-10-12	3	\N
5052	4983	missing	annual_physical	65	2026-10-12	3	\N
5053	4984	missing	annual_physical	65	2026-10-12	3	\N
5054	4985	missing	annual_physical	65	2026-10-12	3	\N
5055	4986	missing	annual_physical	65	2026-10-12	3	\N
5056	4987	missing	annual_physical	65	2026-10-12	3	\N
5057	4988	missing	annual_physical	65	2026-10-12	3	\N
5058	4989	missing	annual_physical	65	2026-10-12	3	\N
5059	4990	missing	annual_physical	65	2026-10-12	3	\N
5060	4991	missing	annual_physical	65	2026-10-12	3	\N
5061	4992	missing	annual_physical	65	2026-10-12	3	\N
5062	4993	missing	annual_physical	65	2026-10-12	3	\N
5063	4994	missing	annual_physical	65	2026-10-12	3	\N
5064	4995	missing	annual_physical	65	2026-10-12	3	\N
5065	4996	missing	annual_physical	65	2026-10-12	3	\N
5066	4997	missing	annual_physical	65	2026-10-12	3	\N
5067	4998	missing	annual_physical	65	2026-10-12	3	\N
5068	4999	missing	annual_physical	65	2026-10-12	3	\N
5069	5000	missing	annual_physical	65	2026-10-12	3	\N
5070	5001	missing	annual_physical	65	2026-10-12	3	\N
5071	5002	missing	annual_physical	65	2026-10-12	3	\N
5072	5003	missing	annual_physical	65	2026-10-12	3	\N
5073	5004	missing	annual_physical	65	2026-10-12	3	\N
5074	5005	missing	annual_physical	65	2026-10-12	3	\N
5075	5006	missing	annual_physical	65	2026-10-12	3	\N
5076	5007	missing	annual_physical	65	2026-10-12	3	\N
5077	5008	missing	annual_physical	65	2026-10-12	3	\N
5078	5009	missing	annual_physical	65	2026-10-12	3	\N
5079	5010	missing	annual_physical	65	2026-10-12	3	\N
5080	5011	missing	annual_physical	65	2026-10-12	3	\N
5081	5012	missing	annual_physical	65	2026-10-12	3	\N
5082	5013	missing	annual_physical	65	2026-10-12	3	\N
5083	5014	missing	annual_physical	65	2026-10-12	3	\N
5084	5015	missing	annual_physical	65	2026-10-12	3	\N
5085	5016	missing	annual_physical	65	2026-10-12	3	\N
5086	5017	missing	annual_physical	65	2026-10-12	3	\N
5087	5018	missing	annual_physical	65	2026-10-12	3	\N
5088	5019	missing	annual_physical	65	2026-10-12	3	\N
5089	5020	missing	annual_physical	65	2026-10-12	3	\N
5090	5021	missing	annual_physical	65	2026-10-12	3	\N
5091	5022	missing	annual_physical	65	2026-10-12	3	\N
5092	5023	missing	annual_physical	65	2026-10-12	3	\N
5093	5024	missing	annual_physical	65	2026-10-12	3	\N
5094	5025	missing	annual_physical	65	2026-10-12	3	\N
5095	5026	missing	annual_physical	65	2026-10-12	3	\N
5096	5027	missing	annual_physical	65	2026-10-12	3	\N
5097	5028	missing	annual_physical	65	2026-10-12	3	\N
5098	5029	missing	annual_physical	65	2026-10-12	3	\N
5099	5030	missing	annual_physical	65	2026-10-12	3	\N
5100	5031	missing	annual_physical	65	2026-10-12	3	\N
5101	5032	missing	annual_physical	65	2026-10-12	3	\N
5102	5033	missing	annual_physical	65	2026-10-12	3	\N
5103	5034	missing	annual_physical	65	2026-10-12	3	\N
5104	5035	missing	annual_physical	65	2026-10-12	3	\N
5105	5036	missing	annual_physical	65	2026-10-12	3	\N
5106	5037	missing	annual_physical	65	2026-10-12	3	\N
5107	5038	missing	annual_physical	65	2026-10-12	3	\N
5108	5039	missing	annual_physical	65	2026-10-12	3	\N
5109	5040	missing	annual_physical	65	2026-10-12	3	\N
5110	5041	missing	annual_physical	65	2026-10-12	3	\N
5111	5042	missing	annual_physical	65	2026-10-12	3	\N
5112	5043	missing	annual_physical	65	2026-10-12	3	\N
5113	5044	missing	annual_physical	65	2026-10-12	3	\N
5114	5045	missing	annual_physical	65	2026-10-12	3	\N
5115	5046	missing	annual_physical	65	2026-10-12	3	\N
5116	5047	missing	annual_physical	65	2026-10-12	3	\N
5117	5048	missing	annual_physical	65	2026-10-12	3	\N
5118	5049	missing	annual_physical	65	2026-10-12	3	\N
5119	5050	missing	annual_physical	65	2026-10-12	3	\N
5120	5051	missing	annual_physical	65	2026-10-12	3	\N
5121	5052	missing	annual_physical	65	2026-10-12	3	\N
5122	5053	missing	annual_physical	65	2026-10-12	3	\N
5123	5054	missing	annual_physical	65	2026-10-12	3	\N
5124	5055	missing	annual_physical	65	2026-10-12	3	\N
5125	5056	missing	annual_physical	65	2026-10-12	3	\N
5126	5057	missing	annual_physical	65	2026-10-12	3	\N
5127	5058	missing	annual_physical	65	2026-10-12	3	\N
5128	5059	missing	annual_physical	65	2026-10-12	3	\N
5129	5060	missing	annual_physical	65	2026-10-12	3	\N
5130	5061	missing	annual_physical	65	2026-10-12	3	\N
5131	5062	missing	annual_physical	65	2026-10-12	3	\N
5132	5063	missing	annual_physical	65	2026-10-12	3	\N
5133	5064	missing	annual_physical	65	2026-10-12	3	\N
5134	5065	missing	annual_physical	65	2026-10-12	3	\N
5135	5066	missing	annual_physical	65	2026-10-12	3	\N
5136	5067	missing	annual_physical	65	2026-10-12	3	\N
5137	5068	missing	annual_physical	65	2026-10-12	3	\N
5138	5069	missing	annual_physical	65	2026-10-12	3	\N
5139	5070	missing	annual_physical	65	2026-10-12	3	\N
5140	5071	missing	annual_physical	65	2026-10-12	3	\N
5141	5072	missing	annual_physical	65	2026-10-12	3	\N
5142	5073	missing	annual_physical	65	2026-10-12	3	\N
5143	5074	missing	annual_physical	65	2026-10-12	3	\N
5144	5075	missing	annual_physical	65	2026-10-12	3	\N
5145	5076	missing	annual_physical	65	2026-10-12	3	\N
5146	5077	missing	annual_physical	65	2026-10-12	3	\N
5147	5078	missing	annual_physical	65	2026-10-12	3	\N
5148	5079	missing	annual_physical	65	2026-10-12	3	\N
5149	5080	missing	annual_physical	65	2026-10-12	3	\N
5150	5081	missing	annual_physical	65	2026-10-12	3	\N
5151	5082	missing	annual_physical	65	2026-10-12	3	\N
5152	5083	missing	annual_physical	65	2026-10-12	3	\N
5153	5084	missing	annual_physical	65	2026-10-12	3	\N
5154	5085	missing	annual_physical	65	2026-10-12	3	\N
5155	5086	missing	annual_physical	65	2026-10-12	3	\N
5156	5087	missing	annual_physical	65	2026-10-12	3	\N
5157	5088	missing	annual_physical	65	2026-10-12	3	\N
5158	5089	missing	annual_physical	65	2026-10-12	3	\N
5159	5090	missing	annual_physical	65	2026-10-12	3	\N
5160	5091	missing	annual_physical	65	2026-10-12	3	\N
5161	5092	missing	annual_physical	65	2026-10-12	3	\N
5162	5093	missing	annual_physical	65	2026-10-12	3	\N
5163	5094	missing	annual_physical	65	2026-10-12	3	\N
5164	5095	missing	annual_physical	65	2026-10-12	3	\N
5165	5096	missing	annual_physical	65	2026-10-12	3	\N
5166	5097	missing	annual_physical	65	2026-10-12	3	\N
5167	5098	missing	annual_physical	65	2026-10-12	3	\N
5168	5099	missing	annual_physical	65	2026-10-12	3	\N
5169	5100	missing	annual_physical	65	2026-10-12	3	\N
5170	5102	missing	annual_physical	65	2026-10-12	3	\N
5171	5103	missing	annual_physical	65	2026-10-12	3	\N
5172	5104	missing	annual_physical	65	2026-10-12	3	\N
\.


--
-- Data for Name: library_settings; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.library_settings (setting_key, setting_value, description, updated_at, updated_by) FROM stdin;
MAX_BORROW_LIMIT_STUDENT	3	Max active loans for students	2026-10-08 01:12:58.180556	1
MAX_BORROW_LIMIT_FACULTY	5	Max active loans for faculty	2026-10-08 01:12:58.181516	1
OVERNIGHT_DUE_DAYS_STUDENT	1	Overnight loan due days for students	2026-10-08 01:12:58.182355	1
OVERNIGHT_DUE_DAYS_FACULTY	7	Overnight loan due days for faculty	2026-10-08 01:12:58.183824	1
DAILY_CIRCULATION_DUE_DAYS	0	Daily circulation due days (0 = same day)	2026-10-08 01:12:58.184744	1
OVERDUE_FINE_PER_DAY	5.0	Overdue fine in pesos per day	2026-10-08 01:12:58.185512	1
OVERDUE_GRACE_DAYS	0	Grace days before fines accrue	2026-10-08 01:12:58.186426	1
RESERVATION_CLAIM_DAYS	2	Days to claim an allocated reservation (legacy fallback)	2026-10-08 01:12:58.187419	1
RESERVATION_CLAIM_HOURS	2.0	Hours to claim an allocated reservation (2-hour pickup window)	2026-10-08 01:12:58.188462	1
DUE_SOON_NOTIFY_DAYS	2	Days before due date to send due-soon reminders	2026-10-08 01:12:58.190265	1
LIBRARY_OPENING_TIME	01:00	Daily opening hour (HH:MM, 24-hour)	2026-10-08 01:12:58.192846	1
LIBRARY_CLOSING_TIME	23:59	Daily closing hour (HH:MM, 24-hour)	2026-10-08 01:12:58.193344	1
\.


--
-- Data for Name: notification_log; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.notification_log (notification_id, recipient_id, message, notif_type, related_reference, is_read, date_sent, updated_at, updated_by) FROM stdin;
20	55	[SEEDSUP] Your book request was approved.	request_update	1	f	2026-10-12 21:55:43.29135	\N	\N
21	56	[SEEDSUP] Overdue: please return your book to avoid further fines.	overdue_reminder	2	f	2026-10-12 21:55:43.29135	\N	\N
22	57	[SEEDSUP] A reserved copy is ready for pickup.	hold_ready	3	f	2026-10-12 21:55:43.29135	\N	\N
23	58	[SEEDSUP] You borrowed a book. Due soon.	borrow	4	f	2026-10-12 21:55:43.29135	\N	\N
24	55	[SEEDSUP] You returned your book. Thank you!	return	5	f	2026-10-12 21:55:43.29135	\N	\N
25	56	[SEEDSUP] Overdue fine assessed. Please settle at the desk.	fine	6	f	2026-10-12 21:55:43.29135	\N	\N
26	57	[SEEDSUP] Reminder: your book is due in 2 days.	due_soon	7	f	2026-10-12 21:55:43.29135	\N	\N
27	58	[SEEDSUP] Reservation placed. You will be notified when ready.	reservation	8	f	2026-10-12 21:55:43.29135	\N	\N
28	55	[SEEDSUP] Your account status was updated.	status_update	9	f	2026-10-12 21:55:43.29135	\N	\N
29	55	Book request for "Dune" submitted and pending review.	request_update	40	f	2026-10-12 21:59:21.379697	\N	\N
30	55	Your book request for "Dune" was approved. Remarks: Demo approval	request_update	40	f	2026-10-12 21:59:21.484878	\N	\N
31	56	You borrowed copy 0629. Due Oct 12, 2026 · 11:59 PM.	borrow	629	f	2026-10-12 21:59:23.986026	\N	\N
32	55	Reservation for "Podcasting: A Practical Guide" placed (queue #1). You will be notified when ready.	reservation	50	f	2026-10-12 21:59:24.08402	\N	\N
33	55	You borrowed "Calculus: Early Transcendentals". Due Oct 12, 2026 · 11:59 PM.	borrow	1347	f	2026-10-12 21:59:24.179948	\N	\N
34	55	Reminder: "Calculus: Early Transcendentals" is due Oct 12, 2026 · 11:59 PM (in 0 day(s)).	due_soon	323	f	2026-10-12 21:59:24.200576	\N	\N
35	55	You returned copy 1347. Thank you!	return	323	f	2026-10-12 21:59:24.309029	\N	\N
\.


--
-- Data for Name: procurement_log; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.procurement_log (procurement_id, request_id, order_status, order_date, date_received, book_id, remarks, updated_at, updated_by) FROM stdin;
13	38	for_ordering	2026-10-02	\N	\N	\N	\N	\N
14	39	ordered	2026-10-02	\N	\N	PO-2026-001 sent to supplier	\N	\N
15	27	delivered	2026-10-02	2026-10-10	\N	Arrived at receiving	\N	\N
16	28	procured	2026-10-02	2026-10-11	1	Cataloged	\N	\N
17	29	cancelled	2026-10-02	\N	\N	Out of budget this term	\N	\N
18	30	out_of_stock	2026-10-02	\N	\N	Supplier has no stock	\N	\N
19	40	ordered	2026-10-12	\N	\N	\N	2026-10-12 21:59:21.496966	65
\.


--
-- Data for Name: request_records; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.request_records (request_id, requester_id, book_title, author, matched_book_id, request_status, request_date, reviewed_by, review_date, remarks, updated_at, updated_by) FROM stdin;
31	59	Introduction to Data Science	Joel Grus	\N	pending_review	2026-10-12 21:55:42.403026	\N	\N	\N	\N	\N
32	55	Philippine History: A New Narrative	Maria Santos	\N	pending_review	2026-10-12 21:55:42.403026	\N	\N	\N	\N	\N
33	56	Philippine History: A New Narrative	Maria Santos	\N	pending_review	2026-10-12 21:55:42.403026	\N	\N	\N	\N	\N
34	58	Philippine History: A New Narrative	Maria Santos	\N	pending_review	2026-10-12 21:55:42.403026	\N	\N	\N	\N	\N
35	56	Clean Architecture in Practice	Robert C. Martin	\N	pending_review	2026-10-12 21:55:42.403026	\N	\N	\N	\N	\N
36	57	Clean Architecture in Practice	Robert C. Martin	\N	pending_review	2026-10-12 21:55:42.403026	\N	\N	\N	\N	\N
37	59	Advanced Research Methods	John Creswell	\N	pending_review	2026-10-12 21:55:42.403026	\N	\N	\N	\N	\N
38	57	Creative Writing for Beginners	Ana Reyes	\N	approved	2026-10-12 21:55:42.403026	1	2026-10-12 21:55:42.403026	\N	\N	\N
39	58	Creative Writing for Beginners	Ana Reyes	\N	approved	2026-10-12 21:55:42.403026	1	2026-10-12 21:55:42.403026	\N	\N	\N
27	55	Introduction to Data Science	Joel Grus	\N	approved	2026-10-12 21:55:42.403026	1	2026-10-12 21:55:43.29135	\N	\N	\N
28	56	Introduction to Data Science	Joel Grus	\N	approved	2026-10-12 21:55:42.403026	1	2026-10-12 21:55:43.29135	\N	\N	\N
29	57	Introduction to Data Science	Joel Grus	\N	approved	2026-10-12 21:55:42.403026	1	2026-10-12 21:55:43.29135	\N	\N	\N
30	58	Introduction to Data Science	Joel Grus	\N	approved	2026-10-12 21:55:42.403026	1	2026-10-12 21:55:43.29135	\N	\N	\N
40	55	Dune	Frank Herbert	\N	approved	2026-10-12 21:59:21.37541	65	2026-10-12 21:59:21.481268	Demo approval	2026-10-12 21:59:21.481268	65
\.


--
-- Data for Name: reservation_queue; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.reservation_queue (reservation_id, book_id, borrower_id, queue_position, request_date, reservation_status, claim_deadline, updated_at, updated_by) FROM stdin;
9	1	75	1	2026-10-12 21:55:43.29135	waiting	\N	\N	\N
10	2	75	1	2026-10-12 21:55:43.29135	allocated	\N	\N	\N
11	3	75	1	2026-10-12 21:55:43.29135	claimed	\N	\N	\N
12	4	75	1	2026-10-12 21:55:43.29135	expired	\N	\N	\N
13	50	55	1	2026-10-12 21:59:24.08289	waiting	\N	\N	\N
\.


--
-- Data for Name: roles; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.roles (role_id, role_name, permissions) FROM stdin;
1	Student	\N
2	Faculty	\N
3	Librarian	\N
4	Admin	\N
\.


--
-- Data for Name: user_accounts; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.user_accounts (user_id, email, oauth_sub, full_name, role_id, account_status, created_at, updated_at, updated_by) FROM stdin;
1	majenifer.labag@mcst.edu.ph	seed_books_oauth	Majenifer Labag	3	active	2026-10-08 00:52:10.567477	\N	\N
60	seedreq_student1@mcst.edu.ph	seedreq_oauth_seedreq_student1	Demo Student One	1	active	2026-10-12 21:55:42.403026	2026-10-12 21:59:32.400767	60
61	seedreq_student2@mcst.edu.ph	seedreq_oauth_seedreq_student2	Demo Student Two	1	active	2026-10-12 21:55:42.403026	\N	\N
62	seedreq_student3@mcst.edu.ph	seedreq_oauth_seedreq_student3	Demo Student Three	1	active	2026-10-12 21:55:42.403026	\N	\N
63	seedreq_faculty1@mcst.edu.ph	seedreq_oauth_seedreq_faculty1	Demo Faculty One	2	active	2026-10-12 21:55:42.403026	\N	\N
64	seedreq_faculty2@mcst.edu.ph	seedreq_oauth_seedreq_faculty2	Demo Faculty Two	2	active	2026-10-12 21:55:42.403026	\N	\N
65	seedreq_librarian1@mcst.edu.ph	seedreq_oauth_seedreq_librarian1	Demo Librarian	3	active	2026-10-12 21:55:42.403026	\N	\N
66	seedreq_admin1@mcst.edu.ph	seedreq_oauth_seedreq_admin1	Demo Admin	4	active	2026-10-12 21:55:42.403026	\N	\N
67	seed100_01@mcst.edu.ph	seed100_oauth_01	Alex Santos	1	active	2026-10-12 21:55:42.749231	\N	\N
68	seed100_02@mcst.edu.ph	seed100_oauth_02	Maria Bautista	1	active	2026-10-12 21:55:42.749231	\N	\N
69	seed100_03@mcst.edu.ph	seed100_oauth_03	Jose Mendoza	1	active	2026-10-12 21:55:42.749231	\N	\N
70	seed100_04@mcst.edu.ph	seed100_oauth_04	Ana Aquino	1	active	2026-10-12 21:55:42.749231	\N	\N
71	seed100_05@mcst.edu.ph	seed100_oauth_05	Mark Santos	1	active	2026-10-12 21:55:42.749231	\N	\N
72	seed100_06@mcst.edu.ph	seed100_oauth_06	Liza Bautista	1	active	2026-10-12 21:55:42.749231	\N	\N
73	seed100_07@mcst.edu.ph	seed100_oauth_07	John Mendoza	1	active	2026-10-12 21:55:42.749231	\N	\N
74	seed100_08@mcst.edu.ph	seed100_oauth_08	Rosa Aquino	1	active	2026-10-12 21:55:42.749231	\N	\N
75	seed100_09@mcst.edu.ph	seed100_oauth_09	Paolo Santos	1	active	2026-10-12 21:55:42.749231	\N	\N
76	seed100_10@mcst.edu.ph	seed100_oauth_10	Nina Bautista	2	active	2026-10-12 21:55:42.749231	\N	\N
77	seed100_11@mcst.edu.ph	seed100_oauth_11	Carlos Mendoza	2	active	2026-10-12 21:55:42.749231	\N	\N
78	seed100_12@mcst.edu.ph	seed100_oauth_12	Ella Aquino	2	active	2026-10-12 21:55:42.749231	\N	\N
79	seedsup_archived@mcst.edu.ph	seedsup_oauth_seedsup_archived	Archived Alma	1	archived	2026-10-12 21:55:43.29135	\N	\N
80	seedsup_disabled@mcst.edu.ph	seedsup_oauth_seedsup_disabled	Disabled Diego	1	disabled	2026-10-12 21:55:43.29135	\N	\N
81	seedsup_pendingfac@mcst.edu.ph	seedsup_oauth_seedsup_pendingfac	Pending Paula	2	pending	2026-10-12 21:55:43.29135	\N	\N
82	seedsup_active@mcst.edu.ph	seedsup_oauth_seedsup_active	Active Andy	1	active	2026-10-12 21:55:43.29135	\N	\N
\.


--
-- Data for Name: user_favorites; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.user_favorites (favorite_id, user_id, book_id, created_at) FROM stdin;
1	1	1	2026-10-08 00:54:18.355751
3	1	3	2026-10-08 00:54:18.355751
10	60	2	2026-10-12 21:55:43.29135
12	60	4	2026-10-12 21:55:43.29135
\.


--
-- Name: accession_log_accession_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.accession_log_accession_id_seq', 5104, true);


--
-- Name: analytics_cache_cache_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.analytics_cache_cache_id_seq', 5, true);


--
-- Name: audit_trail_log_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.audit_trail_log_id_seq', 34, true);


--
-- Name: backup_log_backup_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.backup_log_backup_id_seq', 1, true);


--
-- Name: book_catalog_book_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.book_catalog_book_id_seq', 413, true);


--
-- Name: borrowers_borrower_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.borrowers_borrower_id_seq', 75, true);


--
-- Name: circulation_records_circulation_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.circulation_records_circulation_id_seq', 323, true);


--
-- Name: departments_department_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.departments_department_id_seq', 36, true);


--
-- Name: inventory_sessions_session_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.inventory_sessions_session_id_seq', 3, true);


--
-- Name: inventory_status_inventory_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.inventory_status_inventory_id_seq', 5172, true);


--
-- Name: notification_log_notification_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.notification_log_notification_id_seq', 35, true);


--
-- Name: procurement_log_procurement_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.procurement_log_procurement_id_seq', 19, true);


--
-- Name: request_records_request_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.request_records_request_id_seq', 40, true);


--
-- Name: reservation_queue_reservation_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.reservation_queue_reservation_id_seq', 13, true);


--
-- Name: roles_role_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.roles_role_id_seq', 80, true);


--
-- Name: user_accounts_user_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.user_accounts_user_id_seq', 82, true);


--
-- Name: user_favorites_favorite_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.user_favorites_favorite_id_seq', 12, true);


--
-- Name: accession_log accession_log_accession_number_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.accession_log
    ADD CONSTRAINT accession_log_accession_number_key UNIQUE (accession_number);


--
-- Name: accession_log accession_log_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.accession_log
    ADD CONSTRAINT accession_log_pkey PRIMARY KEY (accession_id);


--
-- Name: analytics_cache analytics_cache_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.analytics_cache
    ADD CONSTRAINT analytics_cache_pkey PRIMARY KEY (cache_id);


--
-- Name: audit_trail audit_trail_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.audit_trail
    ADD CONSTRAINT audit_trail_pkey PRIMARY KEY (log_id);


--
-- Name: backup_log backup_log_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.backup_log
    ADD CONSTRAINT backup_log_pkey PRIMARY KEY (backup_id);


--
-- Name: book_catalog book_catalog_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.book_catalog
    ADD CONSTRAINT book_catalog_pkey PRIMARY KEY (book_id);


--
-- Name: borrowers borrowers_id_number_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.borrowers
    ADD CONSTRAINT borrowers_id_number_key UNIQUE (id_number);


--
-- Name: borrowers borrowers_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.borrowers
    ADD CONSTRAINT borrowers_pkey PRIMARY KEY (borrower_id);


--
-- Name: borrowers borrowers_user_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.borrowers
    ADD CONSTRAINT borrowers_user_id_key UNIQUE (user_id);


--
-- Name: circulation_records circulation_records_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.circulation_records
    ADD CONSTRAINT circulation_records_pkey PRIMARY KEY (circulation_id);


--
-- Name: departments departments_dept_type_name_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.departments
    ADD CONSTRAINT departments_dept_type_name_key UNIQUE (dept_type, name);


--
-- Name: departments departments_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.departments
    ADD CONSTRAINT departments_pkey PRIMARY KEY (department_id);


--
-- Name: inventory_sessions inventory_sessions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.inventory_sessions
    ADD CONSTRAINT inventory_sessions_pkey PRIMARY KEY (session_id);


--
-- Name: inventory_status inventory_status_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.inventory_status
    ADD CONSTRAINT inventory_status_pkey PRIMARY KEY (inventory_id);


--
-- Name: library_settings library_settings_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.library_settings
    ADD CONSTRAINT library_settings_pkey PRIMARY KEY (setting_key);


--
-- Name: notification_log notification_log_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.notification_log
    ADD CONSTRAINT notification_log_pkey PRIMARY KEY (notification_id);


--
-- Name: procurement_log procurement_log_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.procurement_log
    ADD CONSTRAINT procurement_log_pkey PRIMARY KEY (procurement_id);


--
-- Name: request_records request_records_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.request_records
    ADD CONSTRAINT request_records_pkey PRIMARY KEY (request_id);


--
-- Name: reservation_queue reservation_queue_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.reservation_queue
    ADD CONSTRAINT reservation_queue_pkey PRIMARY KEY (reservation_id);


--
-- Name: roles roles_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.roles
    ADD CONSTRAINT roles_pkey PRIMARY KEY (role_id);


--
-- Name: roles roles_role_name_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.roles
    ADD CONSTRAINT roles_role_name_key UNIQUE (role_name);


--
-- Name: user_accounts user_accounts_email_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_accounts
    ADD CONSTRAINT user_accounts_email_key UNIQUE (email);


--
-- Name: user_accounts user_accounts_oauth_sub_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_accounts
    ADD CONSTRAINT user_accounts_oauth_sub_key UNIQUE (oauth_sub);


--
-- Name: user_accounts user_accounts_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_accounts
    ADD CONSTRAINT user_accounts_pkey PRIMARY KEY (user_id);


--
-- Name: user_favorites user_favorites_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_favorites
    ADD CONSTRAINT user_favorites_pkey PRIMARY KEY (favorite_id);


--
-- Name: user_favorites user_favorites_user_id_book_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_favorites
    ADD CONSTRAINT user_favorites_user_id_book_id_key UNIQUE (user_id, book_id);


--
-- Name: idx_accession_log_book; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_accession_log_book ON public.accession_log USING btree (book_id);


--
-- Name: idx_accession_log_number; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_accession_log_number ON public.accession_log USING btree (accession_number);


--
-- Name: idx_audit_time; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_audit_time ON public.audit_trail USING btree (log_timestamp);


--
-- Name: idx_audit_user; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_audit_user ON public.audit_trail USING btree (user_id);


--
-- Name: idx_book_catalog_author; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_book_catalog_author ON public.book_catalog USING btree (author);


--
-- Name: idx_book_catalog_isbn; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_book_catalog_isbn ON public.book_catalog USING btree (isbn);


--
-- Name: idx_book_catalog_status; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_book_catalog_status ON public.book_catalog USING btree (catalog_status);


--
-- Name: idx_book_catalog_subject; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_book_catalog_subject ON public.book_catalog USING btree (subject_classification);


--
-- Name: idx_book_catalog_title; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_book_catalog_title ON public.book_catalog USING btree (title);


--
-- Name: idx_book_catalog_year; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_book_catalog_year ON public.book_catalog USING btree (year_published);


--
-- Name: idx_borrowers_department; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_borrowers_department ON public.borrowers USING btree (department);


--
-- Name: idx_circ_accession; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_circ_accession ON public.circulation_records USING btree (accession_id);


--
-- Name: idx_circ_book; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_circ_book ON public.circulation_records USING btree (book_id);


--
-- Name: idx_circ_borrow_date; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_circ_borrow_date ON public.circulation_records USING btree (borrow_date);


--
-- Name: idx_circ_status; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_circ_status ON public.circulation_records USING btree (transaction_status);


--
-- Name: idx_inventory_accession; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_inventory_accession ON public.inventory_status USING btree (accession_id);


--
-- Name: idx_notif_recipient; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_notif_recipient ON public.notification_log USING btree (recipient_id);


--
-- Name: idx_requests_requester; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_requests_requester ON public.request_records USING btree (requester_id);


--
-- Name: idx_requests_status; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_requests_status ON public.request_records USING btree (request_status);


--
-- Name: idx_reservation_book; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_reservation_book ON public.reservation_queue USING btree (book_id);


--
-- Name: idx_reservation_status; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_reservation_status ON public.reservation_queue USING btree (reservation_status);


--
-- Name: idx_user_accounts_role; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_user_accounts_role ON public.user_accounts USING btree (role_id);


--
-- Name: idx_user_accounts_status; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_user_accounts_status ON public.user_accounts USING btree (account_status);


--
-- Name: uq_active_loan_per_accession; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX uq_active_loan_per_accession ON public.circulation_records USING btree (accession_id) WHERE ((transaction_status)::text = ANY ((ARRAY['active'::character varying, 'overdue'::character varying])::text[]));


--
-- Name: uq_active_loan_per_book_borrower; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX uq_active_loan_per_book_borrower ON public.circulation_records USING btree (book_id, borrower_id) WHERE ((transaction_status)::text = ANY ((ARRAY['active'::character varying, 'overdue'::character varying])::text[]));


--
-- Name: uq_active_queue_pos; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX uq_active_queue_pos ON public.reservation_queue USING btree (book_id, queue_position) WHERE ((reservation_status)::text = ANY ((ARRAY['waiting'::character varying, 'allocated'::character varying])::text[]));


--
-- Name: uq_active_reservation_per_book_borrower; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX uq_active_reservation_per_book_borrower ON public.reservation_queue USING btree (book_id, borrower_id) WHERE ((reservation_status)::text = ANY ((ARRAY['waiting'::character varying, 'allocated'::character varying])::text[]));


--
-- Name: uq_pending_req; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX uq_pending_req ON public.request_records USING btree (requester_id, lower(TRIM(BOTH FROM book_title))) WHERE ((request_status)::text = 'pending_review'::text);


--
-- Name: accession_log accession_log_book_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.accession_log
    ADD CONSTRAINT accession_log_book_id_fkey FOREIGN KEY (book_id) REFERENCES public.book_catalog(book_id);


--
-- Name: accession_log accession_log_librarian_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.accession_log
    ADD CONSTRAINT accession_log_librarian_id_fkey FOREIGN KEY (librarian_id) REFERENCES public.user_accounts(user_id);


--
-- Name: accession_log accession_log_updated_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.accession_log
    ADD CONSTRAINT accession_log_updated_by_fkey FOREIGN KEY (updated_by) REFERENCES public.user_accounts(user_id);


--
-- Name: analytics_cache analytics_cache_generated_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.analytics_cache
    ADD CONSTRAINT analytics_cache_generated_by_fkey FOREIGN KEY (generated_by) REFERENCES public.user_accounts(user_id);


--
-- Name: audit_trail audit_trail_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.audit_trail
    ADD CONSTRAINT audit_trail_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.user_accounts(user_id);


--
-- Name: book_catalog book_catalog_updated_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.book_catalog
    ADD CONSTRAINT book_catalog_updated_by_fkey FOREIGN KEY (updated_by) REFERENCES public.user_accounts(user_id);


--
-- Name: borrowers borrowers_updated_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.borrowers
    ADD CONSTRAINT borrowers_updated_by_fkey FOREIGN KEY (updated_by) REFERENCES public.user_accounts(user_id);


--
-- Name: borrowers borrowers_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.borrowers
    ADD CONSTRAINT borrowers_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.user_accounts(user_id);


--
-- Name: circulation_records circulation_records_accession_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.circulation_records
    ADD CONSTRAINT circulation_records_accession_id_fkey FOREIGN KEY (accession_id) REFERENCES public.accession_log(accession_id);


--
-- Name: circulation_records circulation_records_book_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.circulation_records
    ADD CONSTRAINT circulation_records_book_id_fkey FOREIGN KEY (book_id) REFERENCES public.book_catalog(book_id);


--
-- Name: circulation_records circulation_records_borrower_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.circulation_records
    ADD CONSTRAINT circulation_records_borrower_id_fkey FOREIGN KEY (borrower_id) REFERENCES public.borrowers(borrower_id);


--
-- Name: circulation_records circulation_records_processed_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.circulation_records
    ADD CONSTRAINT circulation_records_processed_by_fkey FOREIGN KEY (processed_by) REFERENCES public.user_accounts(user_id);


--
-- Name: circulation_records circulation_records_updated_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.circulation_records
    ADD CONSTRAINT circulation_records_updated_by_fkey FOREIGN KEY (updated_by) REFERENCES public.user_accounts(user_id);


--
-- Name: inventory_sessions inventory_sessions_librarian_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.inventory_sessions
    ADD CONSTRAINT inventory_sessions_librarian_id_fkey FOREIGN KEY (librarian_id) REFERENCES public.user_accounts(user_id);


--
-- Name: inventory_sessions inventory_sessions_updated_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.inventory_sessions
    ADD CONSTRAINT inventory_sessions_updated_by_fkey FOREIGN KEY (updated_by) REFERENCES public.user_accounts(user_id);


--
-- Name: inventory_status inventory_status_accession_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.inventory_status
    ADD CONSTRAINT inventory_status_accession_id_fkey FOREIGN KEY (accession_id) REFERENCES public.accession_log(accession_id);


--
-- Name: inventory_status inventory_status_checked_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.inventory_status
    ADD CONSTRAINT inventory_status_checked_by_fkey FOREIGN KEY (checked_by) REFERENCES public.user_accounts(user_id);


--
-- Name: inventory_status inventory_status_session_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.inventory_status
    ADD CONSTRAINT inventory_status_session_id_fkey FOREIGN KEY (session_id) REFERENCES public.inventory_sessions(session_id);


--
-- Name: library_settings library_settings_updated_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.library_settings
    ADD CONSTRAINT library_settings_updated_by_fkey FOREIGN KEY (updated_by) REFERENCES public.user_accounts(user_id);


--
-- Name: notification_log notification_log_recipient_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.notification_log
    ADD CONSTRAINT notification_log_recipient_id_fkey FOREIGN KEY (recipient_id) REFERENCES public.borrowers(borrower_id);


--
-- Name: notification_log notification_log_updated_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.notification_log
    ADD CONSTRAINT notification_log_updated_by_fkey FOREIGN KEY (updated_by) REFERENCES public.user_accounts(user_id);


--
-- Name: procurement_log procurement_log_book_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.procurement_log
    ADD CONSTRAINT procurement_log_book_id_fkey FOREIGN KEY (book_id) REFERENCES public.book_catalog(book_id);


--
-- Name: procurement_log procurement_log_request_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.procurement_log
    ADD CONSTRAINT procurement_log_request_id_fkey FOREIGN KEY (request_id) REFERENCES public.request_records(request_id);


--
-- Name: procurement_log procurement_log_updated_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.procurement_log
    ADD CONSTRAINT procurement_log_updated_by_fkey FOREIGN KEY (updated_by) REFERENCES public.user_accounts(user_id);


--
-- Name: request_records request_records_matched_book_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.request_records
    ADD CONSTRAINT request_records_matched_book_id_fkey FOREIGN KEY (matched_book_id) REFERENCES public.book_catalog(book_id);


--
-- Name: request_records request_records_requester_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.request_records
    ADD CONSTRAINT request_records_requester_id_fkey FOREIGN KEY (requester_id) REFERENCES public.borrowers(borrower_id);


--
-- Name: request_records request_records_reviewed_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.request_records
    ADD CONSTRAINT request_records_reviewed_by_fkey FOREIGN KEY (reviewed_by) REFERENCES public.user_accounts(user_id);


--
-- Name: request_records request_records_updated_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.request_records
    ADD CONSTRAINT request_records_updated_by_fkey FOREIGN KEY (updated_by) REFERENCES public.user_accounts(user_id);


--
-- Name: reservation_queue reservation_queue_book_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.reservation_queue
    ADD CONSTRAINT reservation_queue_book_id_fkey FOREIGN KEY (book_id) REFERENCES public.book_catalog(book_id);


--
-- Name: reservation_queue reservation_queue_borrower_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.reservation_queue
    ADD CONSTRAINT reservation_queue_borrower_id_fkey FOREIGN KEY (borrower_id) REFERENCES public.borrowers(borrower_id);


--
-- Name: reservation_queue reservation_queue_updated_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.reservation_queue
    ADD CONSTRAINT reservation_queue_updated_by_fkey FOREIGN KEY (updated_by) REFERENCES public.user_accounts(user_id);


--
-- Name: user_accounts user_accounts_role_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_accounts
    ADD CONSTRAINT user_accounts_role_id_fkey FOREIGN KEY (role_id) REFERENCES public.roles(role_id);


--
-- Name: user_accounts user_accounts_updated_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_accounts
    ADD CONSTRAINT user_accounts_updated_by_fkey FOREIGN KEY (updated_by) REFERENCES public.user_accounts(user_id);


--
-- Name: user_favorites user_favorites_book_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_favorites
    ADD CONSTRAINT user_favorites_book_id_fkey FOREIGN KEY (book_id) REFERENCES public.book_catalog(book_id);


--
-- Name: user_favorites user_favorites_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_favorites
    ADD CONSTRAINT user_favorites_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.user_accounts(user_id);


--
-- PostgreSQL database dump complete
--

\unrestrict vo2G7w67oxLKOnsfFx1kMwYHMZpc3qsbZHl5OHl9YIpRIWh6SkdTfAHEvfuhZGC

