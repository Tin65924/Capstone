--
-- PostgreSQL database dump
--

\restrict xbzw0hMN6zc8yfCBBgipDb1zDf8mV05HfkEhMYs4HjO1fmc88Sp0fPW9uQwiRgg

-- Dumped from database version 18.4
-- Dumped by pg_dump version 18.4

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

ALTER TABLE IF EXISTS ONLY public.user_sessions DROP CONSTRAINT IF EXISTS user_sessions_user_id_fkey;
ALTER TABLE IF EXISTS ONLY public.user_favorites DROP CONSTRAINT IF EXISTS user_favorites_user_id_fkey;
ALTER TABLE IF EXISTS ONLY public.user_favorites DROP CONSTRAINT IF EXISTS user_favorites_book_id_fkey;
ALTER TABLE IF EXISTS ONLY public.user_accounts DROP CONSTRAINT IF EXISTS user_accounts_role_id_fkey;
ALTER TABLE IF EXISTS ONLY public.reservation_queue DROP CONSTRAINT IF EXISTS reservation_queue_borrower_id_fkey;
ALTER TABLE IF EXISTS ONLY public.reservation_queue DROP CONSTRAINT IF EXISTS reservation_queue_book_id_fkey;
ALTER TABLE IF EXISTS ONLY public.request_records DROP CONSTRAINT IF EXISTS request_records_reviewed_by_fkey;
ALTER TABLE IF EXISTS ONLY public.request_records DROP CONSTRAINT IF EXISTS request_records_requester_id_fkey;
ALTER TABLE IF EXISTS ONLY public.request_records DROP CONSTRAINT IF EXISTS request_records_matched_book_id_fkey;
ALTER TABLE IF EXISTS ONLY public.procurement_log DROP CONSTRAINT IF EXISTS procurement_log_request_id_fkey;
ALTER TABLE IF EXISTS ONLY public.procurement_log DROP CONSTRAINT IF EXISTS procurement_log_book_id_fkey;
ALTER TABLE IF EXISTS ONLY public.notification_log DROP CONSTRAINT IF EXISTS notification_log_recipient_id_fkey;
ALTER TABLE IF EXISTS ONLY public.library_settings DROP CONSTRAINT IF EXISTS library_settings_updated_by_fkey;
ALTER TABLE IF EXISTS ONLY public.inventory_status DROP CONSTRAINT IF EXISTS inventory_status_session_id_fkey;
ALTER TABLE IF EXISTS ONLY public.inventory_status DROP CONSTRAINT IF EXISTS inventory_status_checked_by_fkey;
ALTER TABLE IF EXISTS ONLY public.inventory_status DROP CONSTRAINT IF EXISTS inventory_status_accession_id_fkey;
ALTER TABLE IF EXISTS ONLY public.inventory_sessions DROP CONSTRAINT IF EXISTS inventory_sessions_librarian_id_fkey;
ALTER TABLE IF EXISTS ONLY public.circulation_records DROP CONSTRAINT IF EXISTS circulation_records_processed_by_fkey;
ALTER TABLE IF EXISTS ONLY public.circulation_records DROP CONSTRAINT IF EXISTS circulation_records_borrower_id_fkey;
ALTER TABLE IF EXISTS ONLY public.circulation_records DROP CONSTRAINT IF EXISTS circulation_records_book_id_fkey;
ALTER TABLE IF EXISTS ONLY public.circulation_records DROP CONSTRAINT IF EXISTS circulation_records_accession_id_fkey;
ALTER TABLE IF EXISTS ONLY public.borrowers DROP CONSTRAINT IF EXISTS borrowers_user_id_fkey;
ALTER TABLE IF EXISTS ONLY public.audit_trail DROP CONSTRAINT IF EXISTS audit_trail_user_id_fkey;
ALTER TABLE IF EXISTS ONLY public.analytics_cache DROP CONSTRAINT IF EXISTS analytics_cache_generated_by_fkey;
ALTER TABLE IF EXISTS ONLY public.accession_log DROP CONSTRAINT IF EXISTS accession_log_librarian_id_fkey;
ALTER TABLE IF EXISTS ONLY public.accession_log DROP CONSTRAINT IF EXISTS accession_log_book_id_fkey;
ALTER TABLE IF EXISTS ONLY public.user_sessions DROP CONSTRAINT IF EXISTS user_sessions_pkey;
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
ALTER TABLE IF EXISTS public.user_sessions ALTER COLUMN session_id DROP DEFAULT;
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
DROP SEQUENCE IF EXISTS public.user_sessions_session_id_seq;
DROP TABLE IF EXISTS public.user_sessions;
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
    log_timestamp timestamp without time zone DEFAULT now() NOT NULL,
    ip_address character varying(45)
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
    CONSTRAINT backup_log_backup_type_check CHECK (((backup_type)::text = ANY (ARRAY[('manual'::character varying)::text, ('scheduled'::character varying)::text]))),
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
    CONSTRAINT book_catalog_catalog_status_check CHECK (((catalog_status)::text = ANY (ARRAY[('active'::character varying)::text, ('archived'::character varying)::text])))
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
    borrower_status character varying(20) DEFAULT 'active'::character varying NOT NULL,
    phone_number character varying(30),
    CONSTRAINT borrowers_borrower_status_check CHECK (((borrower_status)::text = ANY (ARRAY[('active'::character varying)::text, ('blocked'::character varying)::text])))
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
    due_date date,
    return_date date,
    fine_amount numeric(8,2) DEFAULT 0.00 NOT NULL,
    damage_notes text,
    lost_flag boolean DEFAULT false NOT NULL,
    transaction_status character varying(20) NOT NULL,
    fine_paid boolean DEFAULT false NOT NULL,
    CONSTRAINT circulation_records_borrow_type_check CHECK (((borrow_type)::text = ANY (ARRAY[('overnight'::character varying)::text, ('daily_circulation'::character varying)::text]))),
    CONSTRAINT circulation_records_transaction_status_check CHECK (((transaction_status)::text = ANY (ARRAY[('active'::character varying)::text, ('returned'::character varying)::text, ('overdue'::character varying)::text]))),
    CONSTRAINT circulation_records_transaction_type_check CHECK (((transaction_type)::text = ANY (ARRAY[('borrow'::character varying)::text, ('return'::character varying)::text])))
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
    CONSTRAINT departments_dept_type_check CHECK (((dept_type)::text = ANY (ARRAY[('program'::character varying)::text, ('department'::character varying)::text])))
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
    CONSTRAINT inventory_sessions_session_status_check CHECK (((session_status)::text = ANY (ARRAY[('active'::character varying)::text, ('completed'::character varying)::text, ('cancelled'::character varying)::text])))
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
    CONSTRAINT inventory_status_inventory_state_check CHECK (((inventory_state)::text = ANY (ARRAY[('available'::character varying)::text, ('borrowed'::character varying)::text, ('lost'::character varying)::text, ('damaged'::character varying)::text, ('missing'::character varying)::text]))),
    CONSTRAINT inventory_status_inventory_type_check CHECK (((inventory_type)::text = ANY (ARRAY[('realtime_scan'::character varying)::text, ('annual_physical'::character varying)::text])))
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
    date_sent timestamp without time zone DEFAULT now() NOT NULL,
    is_read boolean DEFAULT false NOT NULL,
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
    CONSTRAINT procurement_log_order_status_check CHECK (((order_status)::text = ANY (ARRAY[('for_ordering'::character varying)::text, ('ordered'::character varying)::text, ('delivered'::character varying)::text, ('cancelled'::character varying)::text, ('out_of_stock'::character varying)::text, ('procured'::character varying)::text])))
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
    CONSTRAINT request_records_request_status_check CHECK (((request_status)::text = ANY (ARRAY[('pending_review'::character varying)::text, ('existing_in_collection'::character varying)::text, ('approved'::character varying)::text, ('rejected'::character varying)::text, ('procured'::character varying)::text])))
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
    CONSTRAINT reservation_queue_reservation_status_check CHECK (((reservation_status)::text = ANY (ARRAY[('waiting'::character varying)::text, ('allocated'::character varying)::text, ('claimed'::character varying)::text, ('expired'::character varying)::text])))
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
-- Name: user_sessions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.user_sessions (
    session_id integer NOT NULL,
    user_id integer NOT NULL,
    login_at timestamp without time zone DEFAULT now() NOT NULL,
    logout_at timestamp without time zone,
    last_seen timestamp without time zone DEFAULT now() NOT NULL,
    ip_address character varying(45),
    user_agent character varying(255)
);


ALTER TABLE public.user_sessions OWNER TO postgres;

--
-- Name: user_sessions_session_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.user_sessions_session_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.user_sessions_session_id_seq OWNER TO postgres;

--
-- Name: user_sessions_session_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.user_sessions_session_id_seq OWNED BY public.user_sessions.session_id;


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
-- Name: user_sessions session_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_sessions ALTER COLUMN session_id SET DEFAULT nextval('public.user_sessions_session_id_seq'::regclass);


--
-- Data for Name: accession_log; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.accession_log (accession_id, accession_number, book_id, librarian_id, date_accessioned, source) FROM stdin;
1	2026-00001	1	1	2026-08-09	purchase
2	2026-00002	2	1	2026-08-15	purchase
3	ACC-0001	3	1	2026-08-15	purchase
4	ACC-0002	4	1	2026-08-15	purchase
5	ACC-0003	5	1	2026-08-15	purchase
6	ACC-0004	6	1	2026-08-15	purchase
7	ACC-0005	7	1	2026-08-15	purchase
8	ACC-0006	8	1	2026-08-15	purchase
9	ACC-0007	9	1	2026-08-15	purchase
10	ACC-0008	10	1	2026-08-15	purchase
11	ACC-0009	11	1	2026-08-15	purchase
12	ACC-0010	12	1	2026-08-15	purchase
13	ACC-0011	13	1	2026-08-15	purchase
14	ACC-0012	14	1	2026-08-15	purchase
15	ACC-0013	15	1	2026-08-15	purchase
16	ACC-0014	16	1	2026-08-15	purchase
17	ACC-0015	17	1	2026-08-15	purchase
18	ACC-0016	18	1	2026-08-15	purchase
19	ACC-0017	19	1	2026-08-15	purchase
20	ACC-0018	20	1	2026-08-15	purchase
21	ACC-0019	21	1	2026-08-15	purchase
22	ACC-0020	22	1	2026-08-15	purchase
23	ACC-0021	23	1	2026-08-15	purchase
24	ACC-0022	24	1	2026-08-15	purchase
25	ACC-0023	25	1	2026-08-15	purchase
26	ACC-0024	26	1	2026-08-15	purchase
27	ACC-0025	27	1	2026-08-15	purchase
28	ACC-0026	28	1	2026-08-15	purchase
29	ACC-0027	29	1	2026-08-15	purchase
30	ACC-0028	30	1	2026-08-15	purchase
31	ACC-0029	31	1	2026-08-15	purchase
32	ACC-0030	32	1	2026-08-15	purchase
33	ACC-0031	33	1	2026-08-15	purchase
34	ACC-0032	34	1	2026-08-15	purchase
35	ACC-0033	35	1	2026-08-15	purchase
36	ACC-0034	36	1	2026-08-15	purchase
37	ACC-0035	37	1	2026-08-15	purchase
38	ACC-0036	38	1	2026-08-15	purchase
39	ACC-0037	39	1	2026-08-15	purchase
40	ACC-0038	40	1	2026-08-15	purchase
41	ACC-0039	41	1	2026-08-15	purchase
42	ACC-0040	42	1	2026-08-15	purchase
43	ACC-0041	43	1	2026-08-15	purchase
44	ACC-0042	44	1	2026-08-15	purchase
45	ACC-0043	45	1	2026-08-15	purchase
46	ACC-0044	46	1	2026-08-15	purchase
47	ACC-0045	47	1	2026-08-15	purchase
48	ACC-0046	48	1	2026-08-15	purchase
49	ACC-0047	49	1	2026-08-15	purchase
50	ACC-0048	50	1	2026-08-15	purchase
51	ACC-0049	51	1	2026-08-15	purchase
52	ACC-0050	52	1	2026-08-15	purchase
53	ACC-0051	53	1	2026-08-15	purchase
54	ACC-0052	54	1	2026-08-15	purchase
55	ACC-0053	55	1	2026-08-15	purchase
56	ACC-0054	56	1	2026-08-15	purchase
57	ACC-0055	57	1	2026-08-15	purchase
58	ACC-0056	58	1	2026-08-15	purchase
59	ACC-0057	59	1	2026-08-15	purchase
60	ACC-0058	60	1	2026-08-15	purchase
61	ACC-0059	61	1	2026-08-15	purchase
62	ACC-0060	62	1	2026-08-15	purchase
63	ACC-0061	63	1	2026-08-15	purchase
64	ACC-0062	64	1	2026-08-15	purchase
65	ACC-0063	65	1	2026-08-15	purchase
66	ACC-0064	66	1	2026-08-15	purchase
67	ACC-0065	67	1	2026-08-15	purchase
68	ACC-0066	68	1	2026-08-15	purchase
69	ACC-0067	69	1	2026-08-15	purchase
70	ACC-0068	70	1	2026-08-15	purchase
71	ACC-0069	71	1	2026-08-15	purchase
72	ACC-0070	72	1	2026-08-15	purchase
73	ACC-0071	73	1	2026-08-15	purchase
74	ACC-0072	74	1	2026-08-15	purchase
75	ACC-0073	75	1	2026-08-15	purchase
76	ACC-0074	76	1	2026-08-15	purchase
77	ACC-0075	77	1	2026-08-15	purchase
78	ACC-0076	78	1	2026-08-15	purchase
79	ACC-0077	79	1	2026-08-15	purchase
80	ACC-0078	80	1	2026-08-15	purchase
81	ACC-0079	81	1	2026-08-15	purchase
82	ACC-0080	82	1	2026-08-15	purchase
83	ACC-0081	83	1	2026-08-15	purchase
84	ACC-0082	84	1	2026-08-15	purchase
85	ACC-0083	85	1	2026-08-15	purchase
86	ACC-0084	86	1	2026-08-15	purchase
87	ACC-0085	87	1	2026-08-15	purchase
88	ACC-0086	88	1	2026-08-15	purchase
89	ACC-0087	89	1	2026-08-15	purchase
90	ACC-0088	90	1	2026-08-15	purchase
91	ACC-0089	91	1	2026-08-15	purchase
92	ACC-0090	92	1	2026-08-15	purchase
93	ACC-0091	93	1	2026-08-15	purchase
94	ACC-0092	94	1	2026-08-15	purchase
95	ACC-0093	95	1	2026-08-15	purchase
96	ACC-0094	96	1	2026-08-15	purchase
97	ACC-0095	97	1	2026-08-15	purchase
98	ACC-0096	98	1	2026-08-15	purchase
99	ACC-0097	99	1	2026-08-15	purchase
100	ACC-0098	100	1	2026-08-15	purchase
101	ACC-0099	101	1	2026-08-15	purchase
102	ACC-0100	102	1	2026-08-15	purchase
103	ACC-0101	103	1	2026-08-15	purchase
104	ACC-0102	104	1	2026-08-15	purchase
105	ACC-0103	105	1	2026-08-15	purchase
106	ACC-0104	106	1	2026-08-15	purchase
107	ACC-0105	107	1	2026-08-15	purchase
108	ACC-0106	108	1	2026-08-15	purchase
109	ACC-0107	109	1	2026-08-15	purchase
110	ACC-0108	110	1	2026-08-15	purchase
111	ACC-0109	111	1	2026-08-15	purchase
112	ACC-0110	112	1	2026-08-15	purchase
113	2023-0040	17	1	2026-08-17	\N
114	2023-0041	39	1	2026-08-17	donation
115	ACC-8759	17	1	2026-08-22	purchase
\.


--
-- Data for Name: analytics_cache; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.analytics_cache (cache_id, report_type, filter_params, kpi_data, generated_by, generated_date) FROM stdin;
1	books_borrowed_per_program	{"to": "", "from": "", "preset": "all"}	[["BSIS", 6], ["Admin", 2]]	1	2026-08-15 13:23:06.052938
2	utilization_rate	{"to": "", "from": "", "preset": "all"}	0.0	1	2026-08-15 13:23:06.07325
3	most_borrowed_titles	{"to": "", "from": "", "preset": "all"}	[["Computer Programming 1", 5], ["Introduction to Computing", 3]]	1	2026-08-15 13:23:06.076444
4	underutilized_titles	{"to": "", "from": "", "preset": "all"}	[]	1	2026-08-15 13:23:06.079388
5	books_borrowed_per_program	{"to": "", "from": "", "preset": "all"}	[["BSIS", 7], ["Admin", 2]]	1	2026-08-15 13:40:40.470633
6	utilization_rate	{"to": "", "from": "", "preset": "all"}	0.0	1	2026-08-15 13:40:40.479158
7	most_borrowed_titles	{"to": "", "from": "", "preset": "all"}	[["Computer Programming 1", 5], ["Introduction to Computing", 3], ["1984", 1]]	1	2026-08-15 13:40:40.481747
8	underutilized_titles	{"to": "", "from": "", "preset": "all"}	[["The Little Prince"], ["Introduction to Probability"], ["The Gene: An Intimate History"], ["Thermal Physics"], ["War and Peace"], ["Thermodynamics: An Engineering Approach"], ["Digital Design"], ["Introduction to Algorithms"], ["Introduction to Electrodynamics"], ["Microeconomics"], ["Moby-Dick"], ["Biochemistry"], ["The Alchemist"], ["The Pragmatic Programmer"], ["Digital Minimalism"], ["The Phoenix Project"], ["Pride and Prejudice"], ["Thinking Fast and Slow"], ["Deep Work"], ["Computer Architecture: A Quantitative Approach"], ["University Physics"], ["Calculus: Early Transcendentals"], ["Programming Pearls"], ["Code Complete"], ["A Short History of Nearly Everything"], ["Computer Networking: A Top-Down Approach"], ["The Book Thief"], ["Atomic Habits"], ["Compilers: Principles Techniques and Tools"], ["Classical Mechanics"], ["Meditations"], ["Clean Code"], ["A People's History of the United States"], ["Molecular Biology of the Cell"], ["The Art of Electronics"], ["Outliers: The Story of Success"], ["The Art of War"], ["Frankenstein"], ["Signals and Systems"], ["The Guns of August"], ["Wuthering Heights"], ["The Sociopath Next Door"], ["Guns Germs and Steel"], ["Operating System Concepts"], ["Campbell Biology"], ["The Innovators"], ["Introduction to Robotics"], ["Design Patterns"], ["The Lean Startup"], ["Fahrenheit 451"], ["Jane Eyre"], ["A Brief History of Time"], ["Cosmos"], ["The Kite Runner"], ["The Elegant Universe"], ["Long Walk to Freedom"], ["Principles of Economics"], ["The Elements of Style"], ["Organic Chemistry"], ["Control Systems Engineering"], ["The Art of Computer Programming"], ["I Know Why the Caged Bird Sings"], ["One Hundred Years of Solitude"], ["Freakonomics"], ["Sapiens: A Brief History of Humankind"], ["Good to Great"], ["How to Win Friends and Influence People"], ["Zero to One"], ["The Odyssey"], ["Refactoring"], ["Don Quixote"], ["The Power of Habit"], ["The 7 Habits of Highly Effective People"], ["To Kill a Mockingbird"], ["Networking"], ["Educated"], ["The Tipping Point"], ["Sophie's World"], ["Fluid Mechanics"], ["The Diary of a Young Girl"], ["The C Programming Language"], ["Silent Spring"], ["Steve Jobs"], ["Life of Pi"], ["The Adventures of Huckleberry Finn"], ["On the Origin of Species"], ["The Selfish Gene"], ["Engineering Mechanics: Dynamics"], ["Fundamentals of Thermodynamics"], ["Introduction to Algorithms for Data Mining"], ["Physical Chemistry"], ["Artificial Intelligence: A Modern Approach"], ["Database System Concepts"], ["Elon Musk"], ["The Wealth of Nations"], ["The Great Gatsby"], ["Brave New World"], ["Microelectronic Circuits"], ["Structure and Interpretation of Computer Programs"], ["The Feynman Lectures on Physics"], ["The Hobbit"], ["Thus Spoke Zarathustra"], ["The Immortal Life of Henrietta Lacks"], ["Crime and Punishment"], ["Linear Algebra Done Right"], ["The Mythical Man-Month"], ["Concrete Mathematics"], ["Dracula"], ["The Catcher in the Rye"]]	1	2026-08-15 13:40:40.485538
9	books_borrowed_per_program	{"to": "", "from": "", "preset": "all"}	[["BSIS", 7], ["Admin", 2]]	1	2026-08-15 13:41:00.86441
10	utilization_rate	{"to": "", "from": "", "preset": "all"}	0.0	1	2026-08-15 13:41:00.875526
11	most_borrowed_titles	{"to": "", "from": "", "preset": "all"}	[["Computer Programming 1", 5], ["Introduction to Computing", 3], ["1984", 1]]	1	2026-08-15 13:41:00.879674
12	underutilized_titles	{"to": "", "from": "", "preset": "all"}	[["The Little Prince"], ["Introduction to Probability"], ["The Gene: An Intimate History"], ["Thermal Physics"], ["War and Peace"], ["Thermodynamics: An Engineering Approach"], ["Digital Design"], ["Introduction to Algorithms"], ["Introduction to Electrodynamics"], ["Microeconomics"], ["Moby-Dick"], ["Biochemistry"], ["The Alchemist"], ["The Pragmatic Programmer"], ["Digital Minimalism"], ["The Phoenix Project"], ["Pride and Prejudice"], ["Thinking Fast and Slow"], ["Deep Work"], ["Computer Architecture: A Quantitative Approach"], ["University Physics"], ["Calculus: Early Transcendentals"], ["Programming Pearls"], ["Code Complete"], ["A Short History of Nearly Everything"], ["Computer Networking: A Top-Down Approach"], ["The Book Thief"], ["Atomic Habits"], ["Compilers: Principles Techniques and Tools"], ["Classical Mechanics"], ["Meditations"], ["Clean Code"], ["A People's History of the United States"], ["Molecular Biology of the Cell"], ["The Art of Electronics"], ["Outliers: The Story of Success"], ["The Art of War"], ["Frankenstein"], ["Signals and Systems"], ["The Guns of August"], ["Wuthering Heights"], ["The Sociopath Next Door"], ["Guns Germs and Steel"], ["Operating System Concepts"], ["Campbell Biology"], ["The Innovators"], ["Introduction to Robotics"], ["Design Patterns"], ["The Lean Startup"], ["Fahrenheit 451"], ["Jane Eyre"], ["A Brief History of Time"], ["Cosmos"], ["The Kite Runner"], ["The Elegant Universe"], ["Long Walk to Freedom"], ["Principles of Economics"], ["The Elements of Style"], ["Organic Chemistry"], ["Control Systems Engineering"], ["The Art of Computer Programming"], ["I Know Why the Caged Bird Sings"], ["One Hundred Years of Solitude"], ["Freakonomics"], ["Sapiens: A Brief History of Humankind"], ["Good to Great"], ["How to Win Friends and Influence People"], ["Zero to One"], ["The Odyssey"], ["Refactoring"], ["Don Quixote"], ["The Power of Habit"], ["The 7 Habits of Highly Effective People"], ["To Kill a Mockingbird"], ["Networking"], ["Educated"], ["The Tipping Point"], ["Sophie's World"], ["Fluid Mechanics"], ["The Diary of a Young Girl"], ["The C Programming Language"], ["Silent Spring"], ["Steve Jobs"], ["Life of Pi"], ["The Adventures of Huckleberry Finn"], ["On the Origin of Species"], ["The Selfish Gene"], ["Engineering Mechanics: Dynamics"], ["Fundamentals of Thermodynamics"], ["Introduction to Algorithms for Data Mining"], ["Physical Chemistry"], ["Artificial Intelligence: A Modern Approach"], ["Database System Concepts"], ["Elon Musk"], ["The Wealth of Nations"], ["The Great Gatsby"], ["Brave New World"], ["Microelectronic Circuits"], ["Structure and Interpretation of Computer Programs"], ["The Feynman Lectures on Physics"], ["The Hobbit"], ["Thus Spoke Zarathustra"], ["The Immortal Life of Henrietta Lacks"], ["Crime and Punishment"], ["Linear Algebra Done Right"], ["The Mythical Man-Month"], ["Concrete Mathematics"], ["Dracula"], ["The Catcher in the Rye"]]	1	2026-08-15 13:41:00.883325
13	books_borrowed_per_program	{"to": "", "from": "", "preset": "all"}	[["BSIS", 16], ["Admin", 3]]	1	2026-08-22 09:14:53.149345
14	utilization_rate	{"to": "", "from": "", "preset": "all"}	1.8	1	2026-08-22 09:14:53.170145
15	most_borrowed_titles	{"to": "", "from": "", "preset": "all"}	[["1984", 6], ["Computer Programming 1", 5], ["A Brief History of Time", 3], ["Introduction to Computing", 3], ["A People's History of the United States", 1], ["Biochemistry", 1]]	1	2026-08-22 09:14:53.172888
16	underutilized_titles	{"to": "", "from": "", "preset": "all"}	[["The Little Prince"], ["Introduction to Probability"], ["The Gene: An Intimate History"], ["Thermal Physics"], ["War and Peace"], ["Thermodynamics: An Engineering Approach"], ["Digital Design"], ["Introduction to Algorithms"], ["Introduction to Electrodynamics"], ["Microeconomics"], ["Moby-Dick"], ["The Alchemist"], ["The Pragmatic Programmer"], ["Digital Minimalism"], ["The Phoenix Project"], ["Pride and Prejudice"], ["Thinking Fast and Slow"], ["Deep Work"], ["Computer Architecture: A Quantitative Approach"], ["University Physics"], ["Calculus: Early Transcendentals"], ["Programming Pearls"], ["Code Complete"], ["A Short History of Nearly Everything"], ["Computer Networking: A Top-Down Approach"], ["The Book Thief"], ["Atomic Habits"], ["Compilers: Principles Techniques and Tools"], ["Classical Mechanics"], ["Meditations"], ["Clean Code"], ["Molecular Biology of the Cell"], ["The Art of Electronics"], ["Outliers: The Story of Success"], ["The Art of War"], ["Frankenstein"], ["Signals and Systems"], ["The Guns of August"], ["Wuthering Heights"], ["The Sociopath Next Door"], ["Guns Germs and Steel"], ["Operating System Concepts"], ["Campbell Biology"], ["The Innovators"], ["Introduction to Robotics"], ["Design Patterns"], ["The Lean Startup"], ["Fahrenheit 451"], ["Jane Eyre"], ["Cosmos"], ["The Kite Runner"], ["The Elegant Universe"], ["Long Walk to Freedom"], ["Principles of Economics"], ["The Elements of Style"], ["Organic Chemistry"], ["Control Systems Engineering"], ["The Art of Computer Programming"], ["I Know Why the Caged Bird Sings"], ["One Hundred Years of Solitude"], ["Freakonomics"], ["Sapiens: A Brief History of Humankind"], ["Good to Great"], ["How to Win Friends and Influence People"], ["Zero to One"], ["The Odyssey"], ["Refactoring"], ["Don Quixote"], ["The Power of Habit"], ["The 7 Habits of Highly Effective People"], ["To Kill a Mockingbird"], ["Networking"], ["Educated"], ["The Tipping Point"], ["Sophie's World"], ["Fluid Mechanics"], ["The Diary of a Young Girl"], ["The C Programming Language"], ["Silent Spring"], ["Steve Jobs"], ["Life of Pi"], ["The Adventures of Huckleberry Finn"], ["On the Origin of Species"], ["The Selfish Gene"], ["Engineering Mechanics: Dynamics"], ["Fundamentals of Thermodynamics"], ["Introduction to Algorithms for Data Mining"], ["Physical Chemistry"], ["Artificial Intelligence: A Modern Approach"], ["Database System Concepts"], ["Elon Musk"], ["The Wealth of Nations"], ["The Great Gatsby"], ["Brave New World"], ["Microelectronic Circuits"], ["Structure and Interpretation of Computer Programs"], ["The Feynman Lectures on Physics"], ["The Hobbit"], ["Thus Spoke Zarathustra"], ["The Immortal Life of Henrietta Lacks"], ["Crime and Punishment"], ["Linear Algebra Done Right"], ["The Mythical Man-Month"], ["Concrete Mathematics"], ["Dracula"], ["The Catcher in the Rye"]]	1	2026-08-22 09:14:53.175359
17	most_borrowed_titles	{"to": "2026-08-13", "from": "2026-08-05", "preset": "custom"}	[]	1	2026-08-22 10:58:35.282319
18	books_borrowed_per_program	{"to": "", "from": "", "preset": "all"}	[["BSIS", 17], ["Admin", 3]]	1	2026-08-22 10:59:46.517658
19	utilization_rate	{"to": "", "from": "", "preset": "all"}	2.7	1	2026-08-22 10:59:46.527921
20	most_borrowed_titles	{"to": "", "from": "", "preset": "all"}	[["1984", 6], ["Computer Programming 1", 5], ["A Brief History of Time", 3], ["Introduction to Computing", 3], ["A People's History of the United States", 2], ["Biochemistry", 1]]	1	2026-08-22 10:59:46.532879
21	underutilized_titles	{"to": "", "from": "", "preset": "all"}	[["The Little Prince"], ["Introduction to Probability"], ["The Gene: An Intimate History"], ["Thermal Physics"], ["War and Peace"], ["Thermodynamics: An Engineering Approach"], ["Digital Design"], ["Introduction to Algorithms"], ["Introduction to Electrodynamics"], ["Microeconomics"], ["Moby-Dick"], ["The Alchemist"], ["The Pragmatic Programmer"], ["Digital Minimalism"], ["The Phoenix Project"], ["Pride and Prejudice"], ["Thinking Fast and Slow"], ["Deep Work"], ["Computer Architecture: A Quantitative Approach"], ["University Physics"], ["Calculus: Early Transcendentals"], ["Programming Pearls"], ["Code Complete"], ["A Short History of Nearly Everything"], ["Computer Networking: A Top-Down Approach"], ["The Book Thief"], ["Atomic Habits"], ["Compilers: Principles Techniques and Tools"], ["Classical Mechanics"], ["Meditations"], ["Clean Code"], ["Molecular Biology of the Cell"], ["The Art of Electronics"], ["Outliers: The Story of Success"], ["The Art of War"], ["Frankenstein"], ["Signals and Systems"], ["The Guns of August"], ["Wuthering Heights"], ["The Sociopath Next Door"], ["Guns Germs and Steel"], ["Operating System Concepts"], ["Campbell Biology"], ["The Innovators"], ["Introduction to Robotics"], ["Design Patterns"], ["The Lean Startup"], ["Fahrenheit 451"], ["Jane Eyre"], ["Cosmos"], ["The Kite Runner"], ["The Elegant Universe"], ["Long Walk to Freedom"], ["Principles of Economics"], ["The Elements of Style"], ["Organic Chemistry"], ["Control Systems Engineering"], ["The Art of Computer Programming"], ["I Know Why the Caged Bird Sings"], ["One Hundred Years of Solitude"], ["Freakonomics"], ["Sapiens: A Brief History of Humankind"], ["Good to Great"], ["How to Win Friends and Influence People"], ["Zero to One"], ["The Odyssey"], ["Refactoring"], ["Don Quixote"], ["The Power of Habit"], ["The 7 Habits of Highly Effective People"], ["To Kill a Mockingbird"], ["Networking"], ["Educated"], ["The Tipping Point"], ["Sophie's World"], ["Fluid Mechanics"], ["The Diary of a Young Girl"], ["The C Programming Language"], ["Silent Spring"], ["Steve Jobs"], ["Life of Pi"], ["The Adventures of Huckleberry Finn"], ["On the Origin of Species"], ["The Selfish Gene"], ["Engineering Mechanics: Dynamics"], ["Fundamentals of Thermodynamics"], ["Introduction to Algorithms for Data Mining"], ["Physical Chemistry"], ["Artificial Intelligence: A Modern Approach"], ["Database System Concepts"], ["Elon Musk"], ["The Wealth of Nations"], ["The Great Gatsby"], ["Brave New World"], ["Microelectronic Circuits"], ["Structure and Interpretation of Computer Programs"], ["The Feynman Lectures on Physics"], ["The Hobbit"], ["Thus Spoke Zarathustra"], ["The Immortal Life of Henrietta Lacks"], ["Crime and Punishment"], ["Linear Algebra Done Right"], ["The Mythical Man-Month"], ["Concrete Mathematics"], ["Dracula"], ["The Catcher in the Rye"]]	1	2026-08-22 10:59:46.537928
22	books_borrowed_per_program	{"to": "", "from": "", "preset": "all"}	[["BSIS", 17], ["Admin", 3]]	1	2026-08-22 11:00:01.25799
23	utilization_rate	{"to": "", "from": "", "preset": "all"}	2.7	1	2026-08-22 11:00:01.267726
24	most_borrowed_titles	{"to": "", "from": "", "preset": "all"}	[["1984", 6], ["Computer Programming 1", 5], ["A Brief History of Time", 3], ["Introduction to Computing", 3], ["A People's History of the United States", 2], ["Biochemistry", 1]]	1	2026-08-22 11:00:01.272013
25	underutilized_titles	{"to": "", "from": "", "preset": "all"}	[["The Little Prince"], ["Introduction to Probability"], ["The Gene: An Intimate History"], ["Thermal Physics"], ["War and Peace"], ["Thermodynamics: An Engineering Approach"], ["Digital Design"], ["Introduction to Algorithms"], ["Introduction to Electrodynamics"], ["Microeconomics"], ["Moby-Dick"], ["The Alchemist"], ["The Pragmatic Programmer"], ["Digital Minimalism"], ["The Phoenix Project"], ["Pride and Prejudice"], ["Thinking Fast and Slow"], ["Deep Work"], ["Computer Architecture: A Quantitative Approach"], ["University Physics"], ["Calculus: Early Transcendentals"], ["Programming Pearls"], ["Code Complete"], ["A Short History of Nearly Everything"], ["Computer Networking: A Top-Down Approach"], ["The Book Thief"], ["Atomic Habits"], ["Compilers: Principles Techniques and Tools"], ["Classical Mechanics"], ["Meditations"], ["Clean Code"], ["Molecular Biology of the Cell"], ["The Art of Electronics"], ["Outliers: The Story of Success"], ["The Art of War"], ["Frankenstein"], ["Signals and Systems"], ["The Guns of August"], ["Wuthering Heights"], ["The Sociopath Next Door"], ["Guns Germs and Steel"], ["Operating System Concepts"], ["Campbell Biology"], ["The Innovators"], ["Introduction to Robotics"], ["Design Patterns"], ["The Lean Startup"], ["Fahrenheit 451"], ["Jane Eyre"], ["Cosmos"], ["The Kite Runner"], ["The Elegant Universe"], ["Long Walk to Freedom"], ["Principles of Economics"], ["The Elements of Style"], ["Organic Chemistry"], ["Control Systems Engineering"], ["The Art of Computer Programming"], ["I Know Why the Caged Bird Sings"], ["One Hundred Years of Solitude"], ["Freakonomics"], ["Sapiens: A Brief History of Humankind"], ["Good to Great"], ["How to Win Friends and Influence People"], ["Zero to One"], ["The Odyssey"], ["Refactoring"], ["Don Quixote"], ["The Power of Habit"], ["The 7 Habits of Highly Effective People"], ["To Kill a Mockingbird"], ["Networking"], ["Educated"], ["The Tipping Point"], ["Sophie's World"], ["Fluid Mechanics"], ["The Diary of a Young Girl"], ["The C Programming Language"], ["Silent Spring"], ["Steve Jobs"], ["Life of Pi"], ["The Adventures of Huckleberry Finn"], ["On the Origin of Species"], ["The Selfish Gene"], ["Engineering Mechanics: Dynamics"], ["Fundamentals of Thermodynamics"], ["Introduction to Algorithms for Data Mining"], ["Physical Chemistry"], ["Artificial Intelligence: A Modern Approach"], ["Database System Concepts"], ["Elon Musk"], ["The Wealth of Nations"], ["The Great Gatsby"], ["Brave New World"], ["Microelectronic Circuits"], ["Structure and Interpretation of Computer Programs"], ["The Feynman Lectures on Physics"], ["The Hobbit"], ["Thus Spoke Zarathustra"], ["The Immortal Life of Henrietta Lacks"], ["Crime and Punishment"], ["Linear Algebra Done Right"], ["The Mythical Man-Month"], ["Concrete Mathematics"], ["Dracula"], ["The Catcher in the Rye"]]	1	2026-08-22 11:00:01.276888
26	utilization_rate	{"to": "", "from": "", "preset": "all"}	2.7	1	2026-08-22 11:10:48.037976
27	underutilized_titles	{"to": "", "from": "", "preset": "all"}	[["The Little Prince"], ["Introduction to Probability"], ["The Gene: An Intimate History"], ["Thermal Physics"], ["War and Peace"], ["Thermodynamics: An Engineering Approach"], ["Digital Design"], ["Introduction to Algorithms"], ["Introduction to Electrodynamics"], ["Microeconomics"], ["Moby-Dick"], ["The Alchemist"], ["The Pragmatic Programmer"], ["Digital Minimalism"], ["The Phoenix Project"], ["Pride and Prejudice"], ["Thinking Fast and Slow"], ["Deep Work"], ["Computer Architecture: A Quantitative Approach"], ["University Physics"], ["Calculus: Early Transcendentals"], ["Programming Pearls"], ["Code Complete"], ["A Short History of Nearly Everything"], ["Computer Networking: A Top-Down Approach"], ["The Book Thief"], ["Atomic Habits"], ["Compilers: Principles Techniques and Tools"], ["Classical Mechanics"], ["Meditations"], ["Clean Code"], ["Molecular Biology of the Cell"], ["The Art of Electronics"], ["Outliers: The Story of Success"], ["The Art of War"], ["Frankenstein"], ["Signals and Systems"], ["The Guns of August"], ["Wuthering Heights"], ["The Sociopath Next Door"], ["Guns Germs and Steel"], ["Operating System Concepts"], ["Campbell Biology"], ["The Innovators"], ["Introduction to Robotics"], ["Design Patterns"], ["The Lean Startup"], ["Fahrenheit 451"], ["Jane Eyre"], ["Cosmos"], ["The Kite Runner"], ["The Elegant Universe"], ["Long Walk to Freedom"], ["Principles of Economics"], ["The Elements of Style"], ["Organic Chemistry"], ["Control Systems Engineering"], ["The Art of Computer Programming"], ["I Know Why the Caged Bird Sings"], ["One Hundred Years of Solitude"], ["Freakonomics"], ["Sapiens: A Brief History of Humankind"], ["Good to Great"], ["How to Win Friends and Influence People"], ["Zero to One"], ["The Odyssey"], ["Refactoring"], ["Don Quixote"], ["The Power of Habit"], ["The 7 Habits of Highly Effective People"], ["To Kill a Mockingbird"], ["Networking"], ["Educated"], ["The Tipping Point"], ["Sophie's World"], ["Fluid Mechanics"], ["The Diary of a Young Girl"], ["The C Programming Language"], ["Silent Spring"], ["Steve Jobs"], ["Life of Pi"], ["The Adventures of Huckleberry Finn"], ["On the Origin of Species"], ["The Selfish Gene"], ["Engineering Mechanics: Dynamics"], ["Fundamentals of Thermodynamics"], ["Introduction to Algorithms for Data Mining"], ["Physical Chemistry"], ["Artificial Intelligence: A Modern Approach"], ["Database System Concepts"], ["Elon Musk"], ["The Wealth of Nations"], ["The Great Gatsby"], ["Brave New World"], ["Microelectronic Circuits"], ["Structure and Interpretation of Computer Programs"], ["The Feynman Lectures on Physics"], ["The Hobbit"], ["Thus Spoke Zarathustra"], ["The Immortal Life of Henrietta Lacks"], ["Crime and Punishment"], ["Linear Algebra Done Right"], ["The Mythical Man-Month"], ["Concrete Mathematics"], ["Dracula"], ["The Catcher in the Rye"]]	1	2026-08-22 11:52:00.755547
28	books_borrowed_per_program	{"to": "", "from": "", "preset": "all"}	[["BSIS", 17], ["Admin", 3]]	1	2026-08-22 11:52:00.761528
29	utilization_rate	{"to": "", "from": "", "preset": "all"}	2.7	1	2026-08-22 11:52:00.764194
30	books_borrowed_per_program	{"to": "", "from": "", "preset": "all"}	[["BSIS", 17], ["Admin", 3]]	1	2026-08-22 13:31:55.440862
31	utilization_rate	{"to": "", "from": "", "preset": "all"}	2.7	1	2026-08-22 13:31:55.444137
32	most_borrowed_titles	{"to": "", "from": "", "preset": "all"}	[["1984", 6], ["Computer Programming 1", 5], ["A Brief History of Time", 3], ["Introduction to Computing", 3], ["A People's History of the United States", 2], ["Biochemistry", 1]]	1	2026-08-22 13:31:55.445024
33	underutilized_titles	{"to": "", "from": "", "preset": "all"}	[["The Little Prince"], ["Introduction to Probability"], ["The Gene: An Intimate History"], ["Thermal Physics"], ["War and Peace"], ["Thermodynamics: An Engineering Approach"], ["Digital Design"], ["Introduction to Algorithms"], ["Introduction to Electrodynamics"], ["Microeconomics"], ["Moby-Dick"], ["The Alchemist"], ["The Pragmatic Programmer"], ["Digital Minimalism"], ["The Phoenix Project"], ["Pride and Prejudice"], ["Thinking Fast and Slow"], ["Deep Work"], ["Computer Architecture: A Quantitative Approach"], ["University Physics"], ["Calculus: Early Transcendentals"], ["Programming Pearls"], ["Code Complete"], ["A Short History of Nearly Everything"], ["Computer Networking: A Top-Down Approach"], ["The Book Thief"], ["Atomic Habits"], ["Compilers: Principles Techniques and Tools"], ["Classical Mechanics"], ["Meditations"], ["Clean Code"], ["Molecular Biology of the Cell"], ["The Art of Electronics"], ["Outliers: The Story of Success"], ["The Art of War"], ["Frankenstein"], ["Signals and Systems"], ["The Guns of August"], ["Wuthering Heights"], ["The Sociopath Next Door"], ["Guns Germs and Steel"], ["Operating System Concepts"], ["Campbell Biology"], ["The Innovators"], ["Introduction to Robotics"], ["Design Patterns"], ["The Lean Startup"], ["Fahrenheit 451"], ["Jane Eyre"], ["Cosmos"], ["The Kite Runner"], ["The Elegant Universe"], ["Long Walk to Freedom"], ["Principles of Economics"], ["The Elements of Style"], ["Organic Chemistry"], ["Control Systems Engineering"], ["The Art of Computer Programming"], ["I Know Why the Caged Bird Sings"], ["One Hundred Years of Solitude"], ["Freakonomics"], ["Sapiens: A Brief History of Humankind"], ["Good to Great"], ["How to Win Friends and Influence People"], ["Zero to One"], ["The Odyssey"], ["Refactoring"], ["Don Quixote"], ["The Power of Habit"], ["The 7 Habits of Highly Effective People"], ["To Kill a Mockingbird"], ["Networking"], ["Educated"], ["The Tipping Point"], ["Sophie's World"], ["Fluid Mechanics"], ["The Diary of a Young Girl"], ["The C Programming Language"], ["Silent Spring"], ["Steve Jobs"], ["Life of Pi"], ["The Adventures of Huckleberry Finn"], ["On the Origin of Species"], ["The Selfish Gene"], ["Engineering Mechanics: Dynamics"], ["Fundamentals of Thermodynamics"], ["Introduction to Algorithms for Data Mining"], ["Physical Chemistry"], ["Artificial Intelligence: A Modern Approach"], ["Database System Concepts"], ["Elon Musk"], ["The Wealth of Nations"], ["The Great Gatsby"], ["Brave New World"], ["Microelectronic Circuits"], ["Structure and Interpretation of Computer Programs"], ["The Feynman Lectures on Physics"], ["The Hobbit"], ["Thus Spoke Zarathustra"], ["The Immortal Life of Henrietta Lacks"], ["Crime and Punishment"], ["Linear Algebra Done Right"], ["The Mythical Man-Month"], ["Concrete Mathematics"], ["Dracula"], ["The Catcher in the Rye"]]	1	2026-08-22 13:31:55.445772
34	books_borrowed_per_program	{"to": "2026-08-04", "from": "2026-08-04", "preset": "custom"}	[]	1	2026-08-22 13:34:06.574462
35	utilization_rate	{"to": "2026-08-04", "from": "2026-08-04", "preset": "custom"}	0.0	1	2026-08-22 13:34:06.578417
36	most_borrowed_titles	{"to": "2026-08-04", "from": "2026-08-04", "preset": "custom"}	[]	1	2026-08-22 13:34:06.580439
37	underutilized_titles	{"to": "2026-08-04", "from": "2026-08-04", "preset": "custom"}	[["The Little Prince"], ["Introduction to Probability"], ["The Gene: An Intimate History"], ["Thermal Physics"], ["War and Peace"], ["Thermodynamics: An Engineering Approach"], ["Digital Design"], ["Introduction to Algorithms"], ["1984"], ["Microeconomics"], ["Introduction to Electrodynamics"], ["Moby-Dick"], ["Biochemistry"], ["Introduction to Computing"], ["The Alchemist"], ["The Phoenix Project"], ["Digital Minimalism"], ["The Pragmatic Programmer"], ["Pride and Prejudice"], ["Thinking Fast and Slow"], ["Deep Work"], ["Computer Architecture: A Quantitative Approach"], ["University Physics"], ["Calculus: Early Transcendentals"], ["Programming Pearls"], ["A Short History of Nearly Everything"], ["Code Complete"], ["Computer Networking: A Top-Down Approach"], ["The Book Thief"], ["Atomic Habits"], ["Compilers: Principles Techniques and Tools"], ["Classical Mechanics"], ["Meditations"], ["A People's History of the United States"], ["Clean Code"], ["Molecular Biology of the Cell"], ["The Art of Electronics"], ["Outliers: The Story of Success"], ["Frankenstein"], ["The Art of War"], ["Signals and Systems"], ["Wuthering Heights"], ["The Guns of August"], ["The Sociopath Next Door"], ["Guns Germs and Steel"], ["Operating System Concepts"], ["The Innovators"], ["Campbell Biology"], ["Introduction to Robotics"], ["The Lean Startup"], ["Design Patterns"], ["Fahrenheit 451"], ["Jane Eyre"], ["A Brief History of Time"], ["Cosmos"], ["Long Walk to Freedom"], ["The Elegant Universe"], ["The Kite Runner"], ["The Elements of Style"], ["Principles of Economics"], ["Organic Chemistry"], ["Control Systems Engineering"], ["I Know Why the Caged Bird Sings"], ["The Art of Computer Programming"], ["Freakonomics"], ["One Hundred Years of Solitude"], ["Sapiens: A Brief History of Humankind"], ["How to Win Friends and Influence People"], ["Zero to One"], ["Good to Great"], ["The Odyssey"], ["Refactoring"], ["Don Quixote"], ["The Power of Habit"], ["The 7 Habits of Highly Effective People"], ["Computer Programming 1"], ["To Kill a Mockingbird"], ["Networking"], ["Educated"], ["The Tipping Point"], ["Sophie's World"], ["The Diary of a Young Girl"], ["Fluid Mechanics"], ["The C Programming Language"], ["Steve Jobs"], ["Silent Spring"], ["Life of Pi"], ["The Adventures of Huckleberry Finn"], ["On the Origin of Species"], ["Engineering Mechanics: Dynamics"], ["The Selfish Gene"], ["Fundamentals of Thermodynamics"], ["Introduction to Algorithms for Data Mining"], ["Physical Chemistry"], ["Database System Concepts"], ["Artificial Intelligence: A Modern Approach"], ["Elon Musk"], ["The Wealth of Nations"], ["The Great Gatsby"], ["Brave New World"], ["Microelectronic Circuits"], ["The Feynman Lectures on Physics"], ["Structure and Interpretation of Computer Programs"], ["The Hobbit"], ["Thus Spoke Zarathustra"], ["The Immortal Life of Henrietta Lacks"], ["Crime and Punishment"], ["The Mythical Man-Month"], ["Linear Algebra Done Right"], ["Dracula"], ["Concrete Mathematics"], ["The Catcher in the Rye"]]	1	2026-08-22 13:34:06.582433
38	books_borrowed_per_program	{"to": "", "from": "", "preset": "all"}	[["BSIS", 17], ["Admin", 4]]	1	2026-08-22 13:55:56.19177
39	utilization_rate	{"to": "", "from": "", "preset": "all"}	2.7	1	2026-08-22 13:55:56.201246
40	most_borrowed_titles	{"to": "", "from": "", "preset": "all"}	[["1984", 7], ["Computer Programming 1", 5], ["A Brief History of Time", 3], ["Introduction to Computing", 3], ["A People's History of the United States", 2], ["Biochemistry", 1]]	1	2026-08-22 13:55:56.205859
41	underutilized_titles	{"to": "", "from": "", "preset": "all"}	[["The Little Prince"], ["Introduction to Probability"], ["The Gene: An Intimate History"], ["Thermal Physics"], ["War and Peace"], ["Thermodynamics: An Engineering Approach"], ["Digital Design"], ["Introduction to Algorithms"], ["Introduction to Electrodynamics"], ["Microeconomics"], ["Moby-Dick"], ["The Alchemist"], ["The Pragmatic Programmer"], ["Digital Minimalism"], ["The Phoenix Project"], ["Pride and Prejudice"], ["Thinking Fast and Slow"], ["Deep Work"], ["Computer Architecture: A Quantitative Approach"], ["University Physics"], ["Calculus: Early Transcendentals"], ["Programming Pearls"], ["Code Complete"], ["A Short History of Nearly Everything"], ["Computer Networking: A Top-Down Approach"], ["The Book Thief"], ["Atomic Habits"], ["Compilers: Principles Techniques and Tools"], ["Classical Mechanics"], ["Meditations"], ["Clean Code"], ["Molecular Biology of the Cell"], ["The Art of Electronics"], ["Outliers: The Story of Success"], ["The Art of War"], ["Frankenstein"], ["Signals and Systems"], ["The Guns of August"], ["Wuthering Heights"], ["The Sociopath Next Door"], ["Guns Germs and Steel"], ["Operating System Concepts"], ["Campbell Biology"], ["The Innovators"], ["Introduction to Robotics"], ["Design Patterns"], ["The Lean Startup"], ["Fahrenheit 451"], ["Jane Eyre"], ["Cosmos"], ["The Kite Runner"], ["The Elegant Universe"], ["Long Walk to Freedom"], ["Principles of Economics"], ["The Elements of Style"], ["Organic Chemistry"], ["Control Systems Engineering"], ["The Art of Computer Programming"], ["I Know Why the Caged Bird Sings"], ["One Hundred Years of Solitude"], ["Freakonomics"], ["Sapiens: A Brief History of Humankind"], ["Good to Great"], ["How to Win Friends and Influence People"], ["Zero to One"], ["The Odyssey"], ["Refactoring"], ["Don Quixote"], ["The Power of Habit"], ["The 7 Habits of Highly Effective People"], ["To Kill a Mockingbird"], ["Networking"], ["Educated"], ["The Tipping Point"], ["Sophie's World"], ["Fluid Mechanics"], ["The Diary of a Young Girl"], ["The C Programming Language"], ["Silent Spring"], ["Steve Jobs"], ["Life of Pi"], ["The Adventures of Huckleberry Finn"], ["On the Origin of Species"], ["The Selfish Gene"], ["Engineering Mechanics: Dynamics"], ["Fundamentals of Thermodynamics"], ["Introduction to Algorithms for Data Mining"], ["Physical Chemistry"], ["Artificial Intelligence: A Modern Approach"], ["Database System Concepts"], ["Elon Musk"], ["The Wealth of Nations"], ["The Great Gatsby"], ["Brave New World"], ["Microelectronic Circuits"], ["Structure and Interpretation of Computer Programs"], ["The Feynman Lectures on Physics"], ["The Hobbit"], ["Thus Spoke Zarathustra"], ["The Immortal Life of Henrietta Lacks"], ["Crime and Punishment"], ["Linear Algebra Done Right"], ["The Mythical Man-Month"], ["Concrete Mathematics"], ["Dracula"], ["The Catcher in the Rye"]]	1	2026-08-22 13:55:56.209042
42	books_borrowed_per_program	{"to": "", "from": "", "preset": "all"}	[["BSIS", 17], ["Admin", 4]]	1	2026-08-24 08:34:38.256776
43	utilization_rate	{"to": "", "from": "", "preset": "all"}	2.7	1	2026-08-24 08:34:38.274762
44	most_borrowed_titles	{"to": "", "from": "", "preset": "all"}	[["1984", 7], ["Computer Programming 1", 5], ["A Brief History of Time", 3], ["Introduction to Computing", 3], ["A People's History of the United States", 2], ["Biochemistry", 1]]	1	2026-08-24 08:34:38.278845
45	underutilized_titles	{"to": "", "from": "", "preset": "all"}	[["The Little Prince"], ["Introduction to Probability"], ["The Gene: An Intimate History"], ["Thermal Physics"], ["War and Peace"], ["Thermodynamics: An Engineering Approach"], ["Digital Design"], ["Introduction to Algorithms"], ["Introduction to Electrodynamics"], ["Microeconomics"], ["Moby-Dick"], ["The Alchemist"], ["The Pragmatic Programmer"], ["Digital Minimalism"], ["The Phoenix Project"], ["Pride and Prejudice"], ["Thinking Fast and Slow"], ["Deep Work"], ["Computer Architecture: A Quantitative Approach"], ["University Physics"], ["Calculus: Early Transcendentals"], ["Programming Pearls"], ["Code Complete"], ["A Short History of Nearly Everything"], ["Computer Networking: A Top-Down Approach"], ["The Book Thief"], ["Atomic Habits"], ["Compilers: Principles Techniques and Tools"], ["Classical Mechanics"], ["Meditations"], ["Clean Code"], ["Molecular Biology of the Cell"], ["The Art of Electronics"], ["Outliers: The Story of Success"], ["The Art of War"], ["Frankenstein"], ["Signals and Systems"], ["The Guns of August"], ["Wuthering Heights"], ["The Sociopath Next Door"], ["Guns Germs and Steel"], ["Operating System Concepts"], ["Campbell Biology"], ["The Innovators"], ["Introduction to Robotics"], ["Design Patterns"], ["The Lean Startup"], ["Fahrenheit 451"], ["Jane Eyre"], ["Cosmos"], ["The Kite Runner"], ["The Elegant Universe"], ["Long Walk to Freedom"], ["Principles of Economics"], ["The Elements of Style"], ["Organic Chemistry"], ["Control Systems Engineering"], ["The Art of Computer Programming"], ["I Know Why the Caged Bird Sings"], ["One Hundred Years of Solitude"], ["Freakonomics"], ["Sapiens: A Brief History of Humankind"], ["Good to Great"], ["How to Win Friends and Influence People"], ["Zero to One"], ["The Odyssey"], ["Refactoring"], ["Don Quixote"], ["The Power of Habit"], ["The 7 Habits of Highly Effective People"], ["To Kill a Mockingbird"], ["Networking"], ["Educated"], ["The Tipping Point"], ["Sophie's World"], ["Fluid Mechanics"], ["The Diary of a Young Girl"], ["The C Programming Language"], ["Silent Spring"], ["Steve Jobs"], ["Life of Pi"], ["The Adventures of Huckleberry Finn"], ["On the Origin of Species"], ["The Selfish Gene"], ["Engineering Mechanics: Dynamics"], ["Fundamentals of Thermodynamics"], ["Introduction to Algorithms for Data Mining"], ["Physical Chemistry"], ["Artificial Intelligence: A Modern Approach"], ["Database System Concepts"], ["Elon Musk"], ["The Wealth of Nations"], ["The Great Gatsby"], ["Brave New World"], ["Microelectronic Circuits"], ["Structure and Interpretation of Computer Programs"], ["The Feynman Lectures on Physics"], ["The Hobbit"], ["Thus Spoke Zarathustra"], ["The Immortal Life of Henrietta Lacks"], ["Crime and Punishment"], ["Linear Algebra Done Right"], ["The Mythical Man-Month"], ["Concrete Mathematics"], ["Dracula"], ["The Catcher in the Rye"]]	1	2026-08-24 08:34:38.281855
46	underutilized_titles	{"to": "", "from": "", "preset": "all"}	[["The Little Prince"], ["Introduction to Probability"], ["The Gene: An Intimate History"], ["Thermal Physics"], ["War and Peace"], ["Thermodynamics: An Engineering Approach"], ["Digital Design"], ["Introduction to Algorithms"], ["Introduction to Electrodynamics"], ["Microeconomics"], ["Moby-Dick"], ["The Alchemist"], ["The Pragmatic Programmer"], ["Digital Minimalism"], ["The Phoenix Project"], ["Pride and Prejudice"], ["Thinking Fast and Slow"], ["Deep Work"], ["Computer Architecture: A Quantitative Approach"], ["University Physics"], ["Calculus: Early Transcendentals"], ["Programming Pearls"], ["Code Complete"], ["A Short History of Nearly Everything"], ["Computer Networking: A Top-Down Approach"], ["The Book Thief"], ["Atomic Habits"], ["Compilers: Principles Techniques and Tools"], ["Classical Mechanics"], ["Meditations"], ["Clean Code"], ["Molecular Biology of the Cell"], ["The Art of Electronics"], ["Outliers: The Story of Success"], ["The Art of War"], ["Frankenstein"], ["Signals and Systems"], ["The Guns of August"], ["Wuthering Heights"], ["The Sociopath Next Door"], ["Guns Germs and Steel"], ["Operating System Concepts"], ["Campbell Biology"], ["The Innovators"], ["Introduction to Robotics"], ["Design Patterns"], ["The Lean Startup"], ["Fahrenheit 451"], ["Jane Eyre"], ["Cosmos"], ["The Kite Runner"], ["The Elegant Universe"], ["Long Walk to Freedom"], ["Principles of Economics"], ["The Elements of Style"], ["Organic Chemistry"], ["Control Systems Engineering"], ["The Art of Computer Programming"], ["I Know Why the Caged Bird Sings"], ["One Hundred Years of Solitude"], ["Freakonomics"], ["Sapiens: A Brief History of Humankind"], ["Good to Great"], ["How to Win Friends and Influence People"], ["Zero to One"], ["The Odyssey"], ["Refactoring"], ["Don Quixote"], ["The Power of Habit"], ["The 7 Habits of Highly Effective People"], ["To Kill a Mockingbird"], ["Networking"], ["Educated"], ["The Tipping Point"], ["Sophie's World"], ["Fluid Mechanics"], ["The Diary of a Young Girl"], ["The C Programming Language"], ["Silent Spring"], ["Steve Jobs"], ["Life of Pi"], ["The Adventures of Huckleberry Finn"], ["On the Origin of Species"], ["The Selfish Gene"], ["Engineering Mechanics: Dynamics"], ["Fundamentals of Thermodynamics"], ["Introduction to Algorithms for Data Mining"], ["Physical Chemistry"], ["Artificial Intelligence: A Modern Approach"], ["Database System Concepts"], ["Elon Musk"], ["The Wealth of Nations"], ["The Great Gatsby"], ["Brave New World"], ["Microelectronic Circuits"], ["Structure and Interpretation of Computer Programs"], ["The Feynman Lectures on Physics"], ["The Hobbit"], ["Thus Spoke Zarathustra"], ["The Immortal Life of Henrietta Lacks"], ["Crime and Punishment"], ["Linear Algebra Done Right"], ["The Mythical Man-Month"], ["Concrete Mathematics"], ["Dracula"], ["The Catcher in the Rye"]]	1	2026-09-14 08:40:07.273232
47	books_borrowed_per_program	{"to": "", "from": "", "preset": "all"}	[["BSIS", 20], ["BS Information Systems", 5]]	1	2026-09-14 08:40:07.292689
48	utilization_rate	{"to": "", "from": "", "preset": "all"}	1.82	1	2026-09-14 08:40:07.296418
49	most_borrowed_titles	{"to": "", "from": "", "preset": "all"}	[["1984", 8], ["A Brief History of Time", 6], ["Computer Programming 1", 5], ["Introduction to Computing", 3], ["A People's History of the United States", 2], ["Biochemistry", 1]]	1	2026-09-14 08:40:07.299555
\.


--
-- Data for Name: audit_trail; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.audit_trail (log_id, user_id, activity, session_token, log_timestamp, ip_address) FROM stdin;
1	1	first_login	\N	2026-08-09 20:35:08.892343	\N
2	1	cataloging:add_book	\N	2026-08-09 20:37:04.134077	\N
3	1	inventory:start_session:1	\N	2026-08-09 20:37:46.504723	\N
4	1	inventory:scan:1	\N	2026-08-09 20:37:59.714654	\N
5	1	inventory:mark_damaged:1	\N	2026-08-09 20:38:16.305512	\N
6	1	inventory:complete_session:1	\N	2026-08-09 20:39:15.022485	\N
7	1	inventory:start_session:2	\N	2026-08-09 20:40:18.345947	\N
8	1	inventory:scan:1	\N	2026-08-09 20:40:34.189852	\N
9	1	inventory:scan:1	\N	2026-08-09 20:40:48.372269	\N
10	1	login	\N	2026-08-10 04:02:59.599613	\N
11	1	inventory:cancel_session:2	\N	2026-08-10 04:03:14.517878	\N
12	1	login	\N	2026-08-15 06:49:28.888273	\N
13	1	requests:create:1	\N	2026-08-15 06:49:58.592281	\N
14	1	requests:approve:1	\N	2026-08-15 06:50:17.113546	\N
15	1	procurement:update_status:1	\N	2026-08-15 06:51:03.502105	\N
16	1	procurement:update_status:1	\N	2026-08-15 06:51:07.910842	\N
17	1	inventory:start_session:3	\N	2026-08-15 06:51:52.468528	\N
18	1	inventory:scan:1	\N	2026-08-15 06:52:02.621654	\N
19	1	inventory:complete_session:3	\N	2026-08-15 06:52:08.572852	\N
20	1	login	\N	2026-08-15 08:24:44.632361	\N
21	1	logout	\N	2026-08-15 08:26:17.790684	\N
22	2	first_login	\N	2026-08-15 08:31:50.199995	\N
23	1	login	\N	2026-08-15 08:32:16.537311	\N
24	1	login	\N	2026-08-15 10:06:18.785708	\N
25	1	circulation:user_borrow:1	\N	2026-08-15 10:06:31.503325	\N
26	1	logout	\N	2026-08-15 10:06:47.906154	\N
27	2	login	\N	2026-08-15 10:06:54.922706	\N
28	1	login	\N	2026-08-15 10:07:05.270948	\N
29	2	circulation:user_reserve:1	\N	2026-08-15 10:07:10.223727	\N
30	1	circulation:allocate_reservation:1	\N	2026-08-15 10:08:19.081707	\N
31	1	circulation:claim_reservation:1	\N	2026-08-15 10:08:25.485809	\N
32	2	circulation:user_reserve:1	\N	2026-08-15 10:10:29.404091	\N
33	1	circulation:return:1	\N	2026-08-15 10:11:30.09674	\N
34	2	circulation:user_borrow:1	\N	2026-08-15 10:12:54.645614	\N
35	1	circulation:allocate_reservation:2	\N	2026-08-15 10:13:24.72184	\N
36	2	circulation:user_return:2	\N	2026-08-15 11:04:35.613624	\N
37	1	cataloging:add_book	\N	2026-08-15 11:07:46.853255	\N
38	2	circulation:user_borrow:2	\N	2026-08-15 11:08:02.240042	\N
39	2	circulation:user_return:3	\N	2026-08-15 11:08:56.206726	\N
40	2	circulation:user_borrow:2	\N	2026-08-15 11:09:42.986208	\N
41	1	circulation:user_reserve:2	\N	2026-08-15 11:10:04.600791	\N
42	1	circulation:user_borrow:1	\N	2026-08-15 11:11:13.748451	\N
43	1	circulation:user_return:5	\N	2026-08-15 11:12:00.982015	\N
44	1	circulation:claim_reservation:2	\N	2026-08-15 11:12:41.744296	\N
45	2	circulation:user_return:4	\N	2026-08-15 11:13:02.125156	\N
46	1	circulation:allocate_reservation:3	\N	2026-08-15 11:13:07.046443	\N
47	1	circulation:claim_reservation:3	\N	2026-08-15 11:13:11.718784	\N
48	2	circulation:user_borrow:2	\N	2026-08-15 11:13:32.543782	\N
49	1	circulation:user_reserve:2	\N	2026-08-15 11:13:43.034505	\N
50	2	circulation:user_return:6	\N	2026-08-15 11:14:22.997077	\N
51	1	circulation:allocate_reservation:4	\N	2026-08-15 11:14:28.235889	\N
52	1	circulation:claim_reservation:4	\N	2026-08-15 11:14:33.084933	\N
53	2	circulation:user_borrow:2	\N	2026-08-15 13:14:18.216136	\N
54	1	circulation:user_reserve:2	\N	2026-08-15 13:16:53.451556	\N
55	1	circulation:expire_reservation:5	\N	2026-08-15 13:17:24.446624	\N
56	2	circulation:user_return:7	\N	2026-08-15 13:17:40.487192	\N
57	2	circulation:user_borrow:2	\N	2026-08-15 13:19:20.250914	\N
58	1	circulation:user_reserve:2	\N	2026-08-15 13:19:33.556466	\N
59	2	circulation:user_return:8	\N	2026-08-15 13:20:04.136941	\N
60	1	circulation:allocate_reservation:6	\N	2026-08-15 13:20:18.260724	\N
61	1	circulation:claim_reservation:6	\N	2026-08-15 13:20:23.596232	\N
62	1	cataloging:bulk_import:110_success_0_errors	\N	2026-08-15 13:33:43.488454	\N
63	2	circulation:user_borrow:17	\N	2026-08-15 13:35:24.987116	\N
64	2	circulation:user_return:9	\N	2026-08-15 13:38:40.251366	\N
65	1	logout	\N	2026-08-15 13:46:52.284443	\N
66	2	requests:create:2	\N	2026-08-15 13:48:47.595214	\N
67	2	circulation:user_borrow:17	\N	2026-08-15 13:49:00.409052	\N
68	1	login	\N	2026-08-16 08:25:10.151524	\N
69	1	login	\N	2026-08-17 08:28:21.146304	\N
70	1	logout	\N	2026-08-17 08:28:24.561601	\N
71	2	login	\N	2026-08-17 09:22:11.117254	\N
72	1	login	\N	2026-08-17 09:22:29.187931	\N
73	2	circulation:user_borrow_request:39	\N	2026-08-17 09:23:14.639347	\N
74	1	circulation:allocate_reservation:7	\N	2026-08-17 09:23:41.523092	\N
75	1	circulation:claim_reservation:7	\N	2026-08-17 09:23:46.666648	\N
76	2	login	\N	2026-08-17 09:37:32.071435	\N
77	2	circulation:user_return:11	\N	2026-08-17 09:37:42.197945	\N
78	2	circulation:user_return:10	\N	2026-08-17 09:37:45.759958	\N
79	2	login	\N	2026-08-17 09:54:39.009295	\N
80	1	login	\N	2026-08-17 09:54:55.988654	\N
81	2	circulation:user_borrow:17	\N	2026-08-17 09:58:17.800294	\N
82	2	login	\N	2026-08-17 10:20:10.444281	\N
83	1	login	\N	2026-08-17 10:20:49.167111	\N
84	1	cataloging:toggle_status:91:archived	\N	2026-08-17 10:21:54.159455	\N
85	1	cataloging:add_accession:17	\N	2026-08-17 10:22:24.926703	\N
86	1	cataloging:add_accession:39	\N	2026-08-17 10:23:25.289699	\N
87	2	circulation:user_return:12	\N	2026-08-17 10:24:00.491221	\N
88	2	circulation:user_borrow_request:17	\N	2026-08-17 10:24:24.598192	\N
89	1	circulation:allocate_reservation:8	\N	2026-08-17 10:24:41.754937	\N
90	1	circulation:claim_reservation:8	\N	2026-08-17 10:24:45.6501	\N
91	2	circulation:user_borrow_request:39	\N	2026-08-17 10:26:54.066925	\N
92	1	circulation:allocate_reservation:9	\N	2026-08-17 10:27:17.049858	\N
93	1	circulation:claim_reservation:9	\N	2026-08-17 10:27:26.779521	\N
94	2	circulation:user_borrow_request:68	\N	2026-08-17 10:28:03.147428	\N
95	1	circulation:allocate_reservation:10	\N	2026-08-17 10:28:28.944032	\N
96	1	circulation:claim_reservation:10	\N	2026-08-17 10:28:38.853667	\N
97	2	circulation:user_borrow_request:33	\N	2026-08-17 10:28:57.717453	\N
98	1	circulation:allocate_reservation:11	\N	2026-08-17 10:29:09.745788	\N
99	1	circulation:claim_reservation:11	\N	2026-08-17 10:29:15.730779	\N
100	2	circulation:user_return:13	\N	2026-08-17 10:29:24.195236	\N
101	2	circulation:user_return:16	\N	2026-08-17 10:29:27.692453	\N
102	2	circulation:user_return:14	\N	2026-08-17 10:29:30.029965	\N
103	2	circulation:user_return:15	\N	2026-08-17 10:29:32.019474	\N
104	2	circulation:user_borrow:17	\N	2026-08-17 10:31:49.482018	\N
105	2	circulation:user_borrow_request:17	\N	2026-08-17 10:32:06.422501	\N
106	1	circulation:allocate_reservation:12	\N	2026-08-17 10:32:32.967944	\N
107	1	circulation:claim_reservation:12	\N	2026-08-17 10:32:40.34126	\N
108	2	circulation:user_return:17	\N	2026-08-17 10:33:50.89774	\N
109	1	login	\N	2026-08-21 12:53:39.973334	\N
110	1	circulation:user_borrow_request:39	\N	2026-08-21 13:34:36.537884	\N
111	1	circulation:allocate_reservation:13	\N	2026-08-21 13:35:27.236257	\N
112	1	circulation:claim_reservation:13	\N	2026-08-21 13:35:33.253454	\N
113	1	login	\N	2026-08-21 16:49:40.741133	\N
114	1	login	\N	2026-08-22 09:13:59.170215	\N
115	1	logout	\N	2026-08-22 09:17:13.795878	\N
116	2	login	\N	2026-08-22 09:17:22.82842	\N
117	1	login	\N	2026-08-22 09:17:42.049379	\N
118	2	circulation:user_borrow_request:68	\N	2026-08-22 09:18:17.938681	\N
119	1	circulation:allocate_reservation:14	\N	2026-08-22 09:18:45.216266	\N
120	1	circulation:claim_reservation:14	\N	2026-08-22 09:19:04.067529	\N
121	1	login	\N	2026-08-22 09:31:52.95549	\N
122	1	cataloging:export_books:all:112	\N	2026-08-22 10:52:39.897778	\N
123	1	users:export:all:2	\N	2026-08-22 10:55:11.2021	\N
124	1	login	\N	2026-08-22 13:28:24.288283	\N
125	1	cataloging:export_books:all:112	\N	2026-08-22 13:34:57.847718	\N
126	1	cataloging:bulk_import:110_success_0_errors	\N	2026-08-22 13:36:13.687768	\N
127	1	cataloging:bulk_import:110_success_0_errors	\N	2026-08-22 13:37:01.979073	\N
128	1	cataloging:bulk_import:110_success_0_errors	\N	2026-08-22 13:38:40.360041	\N
129	1	circulation:user_borrow_request:17	\N	2026-08-22 13:41:32.885905	\N
130	1	circulation:allocate_reservation:15	\N	2026-08-22 13:43:34.260163	\N
131	1	circulation:claim_reservation:15	\N	2026-08-22 13:44:37.535145	\N
132	1	circulation:return:21	\N	2026-08-22 13:46:12.903237	\N
133	1	users:export:all:2	\N	2026-08-22 13:47:11.685767	\N
134	1	toggled_user_status:1	\N	2026-08-22 13:47:58.192164	\N
135	1	login	\N	2026-08-22 13:50:28.285383	\N
136	1	login	\N	2026-08-22 13:52:18.995155	\N
137	1	cataloging:export_books:all:112	\N	2026-08-22 13:57:38.619216	\N
138	1	cataloging:export_books:all:112	\N	2026-08-22 13:57:41.253505	\N
139	1	cataloging:export_books:all:112	\N	2026-08-22 13:58:18.336213	\N
140	1	login	\N	2026-08-23 16:49:21.890206	\N
141	1	requests:reject:2	\N	2026-08-23 20:58:56.655787	\N
142	1	login	\N	2026-08-24 08:18:33.762834	\N
143	1	cataloging:toggle_status:68:archived	\N	2026-08-24 08:53:29.769913	\N
144	1	inventory:mark_lost:1	\N	2026-08-24 09:41:20.585917	\N
145	1	login	\N	2026-08-26 08:25:04.279014	\N
146	1	login	\N	2026-08-28 14:00:05.710985	\N
147	1	login	\N	2026-09-02 13:46:30.671126	\N
148	1	login	\N	2026-09-03 15:54:19.392365	\N
149	1	circulation:user_borrow_request:39	\N	2026-09-03 17:04:55.833617	\N
150	1	circulation:expire_reservation:16	\N	2026-09-03 17:07:48.285564	\N
151	1	logout	\N	2026-09-03 17:11:09.605221	\N
152	2	login	\N	2026-09-03 17:11:30.559753	\N
153	2	logout	\N	2026-09-03 17:11:30.889038	\N
154	2	login	\N	2026-09-03 17:11:41.983852	\N
155	1	login	\N	2026-09-03 17:12:39.723206	\N
156	1	circulation:user_borrow_request:39	\N	2026-09-03 17:13:18.030795	\N
157	2	circulation:user_borrow_request:39	\N	2026-09-03 17:14:05.792879	\N
158	1	circulation:expire_reservation:18	\N	2026-09-03 17:16:21.191575	\N
159	2	circulation:user_borrow:39	\N	2026-09-03 17:16:52.213796	\N
160	1	circulation:return:22	\N	2026-09-03 17:18:35.405825	\N
161	1	circulation:return:18	\N	2026-09-03 17:20:20.080496	\N
162	1	login	\N	2026-09-03 20:21:04.187142	\N
163	1	circulation:user_borrow_request:79	\N	2026-09-03 20:34:30.630316	\N
164	1	logout	\N	2026-09-03 20:34:45.268202	\N
165	2	login	\N	2026-09-03 20:34:51.587303	\N
166	1	login	\N	2026-09-03 20:35:09.920602	\N
167	2	circulation:user_borrow_request:39	\N	2026-09-03 20:35:43.747362	\N
168	1	circulation:allocate_reservation:17	\N	2026-09-03 20:35:54.296416	\N
169	1	circulation:claim_reservation:17	\N	2026-09-03 20:36:13.374387	\N
170	2	circulation:user_borrow_request:17	\N	2026-09-03 20:37:30.713554	\N
171	1	circulation:allocate_reservation:21	\N	2026-09-03 20:37:43.418624	\N
172	1	circulation:claim_reservation:21	\N	2026-09-03 20:37:49.820738	\N
173	2	circulation:user_borrow_request:17	\N	2026-09-03 20:40:27.467991	\N
174	1	circulation:return:23	\N	2026-09-03 20:47:34.437342	\N
175	1	login	\N	2026-09-04 11:46:40.205934	\N
176	1	login	\N	2026-09-05 16:51:15.916581	\N
177	1	profile:update	\N	2026-09-05 18:25:26.728736	\N
178	1	circulation:return:20	\N	2026-09-05 18:27:45.621334	\N
179	2	notifications:read:26	\N	2026-09-05 18:28:18.365203	\N
180	2	notifications:read_all	\N	2026-09-05 18:28:29.962799	\N
181	1	login	\N	2026-09-05 20:53:44.003789	\N
182	1	login	\N	2026-09-08 13:54:52.081134	\N
183	1	login	\N	2026-09-13 13:35:29.45699	\N
184	1	circulation:expire_reservation:19	\N	2026-09-13 13:38:48.573145	\N
185	1	circulation:expire_reservation:22	\N	2026-09-13 13:42:07.602862	\N
186	1	circulation:allocate_reservation:20	\N	2026-09-13 13:52:40.065846	\N
187	1	circulation:claim_reservation:20	\N	2026-09-13 14:07:31.971676	\N
188	1	login	\N	2026-09-14 08:30:20.965681	\N
189	1	login	\N	2026-09-18 14:10:46.779105	\N
190	1	notifications:read_all	\N	2026-09-18 14:18:21.605618	\N
191	2	notifications:read_all	\N	2026-09-18 14:18:56.537581	\N
192	1	backup:failed:manual	\N	2026-09-18 14:25:14.745746	\N
193	1	backup:created:library_backup_20260918_142858.sql	\N	2026-09-18 14:28:58.443712	\N
194	1	backup:created:library_backup_20260918_142948.sql	\N	2026-09-18 14:29:48.193939	\N
195	1	backup:restored:library_backup_20260918_144247.sql	\N	2026-09-19 14:09:30.492665	\N
196	1	login	\N	2026-09-21 08:19:34.271093	\N
197	2	logout	\N	2026-09-21 08:32:10.314961	\N
198	2	login	\N	2026-09-21 08:32:21.464017	\N
199	1	cataloging:edit_book:17	\N	2026-09-21 08:32:40.892143	\N
200	1	backup:restored:library_backup_20260921_083657.sql	\N	2026-09-24 09:05:14.74744	\N
201	1	login	\N	2026-09-24 09:29:06.70517	\N
202	1	backup:restore_failed:library_backup_20260918_142948.sql	\N	2026-09-24 09:29:25.594479	\N
203	1	backup:restored:library_backup_20260924_092930.sql	\N	2026-09-24 10:12:07.014551	\N
204	1	login	\N	2026-09-26 09:04:34.82284	\N
\.


--
-- Data for Name: backup_log; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.backup_log (backup_id, filename, size_bytes, status, backup_type, error_msg, created_at) FROM stdin;
1	manual_backup_failed.sql	\N	failed	manual	[WinError 2] The system cannot find the file specified	2026-09-18 14:25:14.745746
2	library_backup_20260918_142858.sql	134798	completed	manual	\N	2026-09-18 14:28:58.443712
3	library_backup_20260918_142948.sql	134975	completed	manual	\N	2026-09-18 14:29:48.193939
5	library_backup_20260924_092924.sql	150818	completed	manual	pre-restore auto-backup	2026-09-24 09:29:25.402092
6	library_backup_20260924_101206.sql	151223	completed	manual	pre-restore auto-backup	2026-09-24 10:12:06.407081
7	library_backup_20260924_095355.sql	151206	completed	manual	pre-restore auto-backup	2026-09-24 09:53:55.777742
8	library_backup_20260924_092930.sql	151026	completed	manual	\N	2026-09-24 09:29:31.404442
4	library_backup_20260921_083657_in_progress.sql	\N	failed	manual	Worker did not finish (stale in-progress run).	2026-09-21 08:36:57.275957
\.


--
-- Data for Name: book_catalog; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.book_catalog (book_id, title, author, edition, publisher, year_published, subject_classification, call_number, isbn, material_type, description, catalog_status, date_added) FROM stdin;
1	Introduction to Computing	Justin Babbage	2nd	MJ et al.,	2023	Computer Programming	QA76.73	175996747	Book	Counting	active	2026-08-09
2	Computer Programming 1	Glenn	1st	Patrick	2025	Computer Programming 1	QA75.78	870606009	Book	NONE	active	2026-08-15
3	Introduction to Algorithms	Thomas H. Cormen	3rd	MIT Press	2009	Computer Science	QA76.6.C66	978-0262033848	Book	Comprehensive textbook on algorithms and data structures	active	2026-08-15
4	Clean Code	Robert C. Martin	1st	Prentice Hall	2008	Software Engineering	QA76.76.R63	978-0132350884	Book	A handbook of agile software craftsmanship	active	2026-08-15
5	The Pragmatic Programmer	David Thomas	2nd	Addison-Wesley	2019	Software Engineering	QA76.6.T45	978-0201616224	Book	Timeless tips for software developers	active	2026-08-15
6	Design Patterns	Erich Gamma	1st	Addison-Wesley	1994	Software Engineering	QA76.64.G36	978-0201633610	Book	Gang of Four design patterns catalog	active	2026-08-15
7	Artificial Intelligence: A Modern Approach	Stuart Russell	4th	Pearson	2020	Artificial Intelligence	Q335.R87	978-0134610993	Book	Comprehensive AI textbook	active	2026-08-15
8	Computer Networking: A Top-Down Approach	James Kurose	7th	Pearson	2016	Computer Science	TK5105.875.I57 K87	978-0133594140	Book	Top-down approach to computer networking	active	2026-08-15
9	Database System Concepts	Abraham Silberschatz	7th	McGraw-Hill	2019	Computer Science	QA76.9.D3 S55	978-0078022159	Book	Fundamentals of database systems	active	2026-08-15
10	Operating System Concepts	Abraham Silberschatz	8th	Wiley	2018	Computer Science	QA76.76.O63 S55	978-0470487341	Book	OS fundamentals textbook	active	2026-08-15
11	The C Programming Language	Brian Kernighan	2nd	Prentice Hall	1988	Computer Science	QA76.73.C15 K47	978-0131103627	Book	Classic C programming reference	active	2026-08-15
12	Structure and Interpretation of Computer Programs	Harold Abelson	2nd	MIT Press	1996	Computer Science	QA76.6.A24	978-0262510875	Book	Foundational CS text using Scheme	active	2026-08-15
13	Don Quixote	Miguel de Cervantes	1st	Harper Perennial	2005	Literature	PQ6329.A1 2005	978-0060934347	Book	Spanish literary classic	active	2026-08-15
14	One Hundred Years of Solitude	Gabriel García Márquez	1st	Harper Perennial	2006	Literature	PQ8180.17.A73	978-0060883287	Book	Magical realism masterpiece	active	2026-08-15
15	The Great Gatsby	F. Scott Fitzgerald	1st	Scribner	2004	Literature	PS3511.I9 G7	978-0743273565	Book	American literary classic	active	2026-08-15
16	To Kill a Mockingbird	Harper Lee	1st	Harper Perennial	2006	Literature	PS3562.E33 T6	978-0061120084	Book	American novel about racial injustice	active	2026-08-15
18	Pride and Prejudice	Jane Austen	1st	Penguin	2002	Literature	PR4034.P7	978-0141439518	Book	Classic romance novel	active	2026-08-15
19	The Catcher in the Rye	J.D. Salinger	1st	Little Brown	1991	Literature	PS3537.A426 C3	978-0316769488	Book	Coming-of-age novel	active	2026-08-15
20	Moby-Dick	Herman Melville	1st	Penguin	2002	Literature	PS2384.M6	978-0142437247	Book	American epic whaling novel	active	2026-08-15
21	War and Peace	Leo Tolstoy	1st	Oxford UP	2008	Literature	PG3366.V6 2008	978-0199232765	Book	Russian historical novel	active	2026-08-15
22	The Odyssey	Homer	1st	Penguin	1999	Literature	PA4025.A5 O3	978-0140268867	Book	Ancient Greek epic poem	active	2026-08-15
23	Calculus: Early Transcendentals	James Stewart	8th	Cengage	2015	Mathematics	QA303.2.S74	978-1285741550	Book	Standard calculus textbook	active	2026-08-15
24	Linear Algebra Done Right	Sheldon Axler	3rd	Springer	2015	Mathematics	QA184.2.A95	978-3319110790	Book	Undergraduate linear algebra text	active	2026-08-15
25	Introduction to Probability	Dimitri Bertsekas	2nd	Athena Scientific	2008	Mathematics	QA273.B48	978-1886529403	Book	Probability theory fundamentals	active	2026-08-15
26	The Feynman Lectures on Physics	Richard Feynman	1st	Basic Books	2010	Physics	QC21.2.F49	978-0465023820	Book	Classic physics lecture series	active	2026-08-15
27	University Physics	Young and Freedman	14th	Pearson	2015	Physics	QC21.3.Y68	978-0133969290	Book	Standard university physics textbook	active	2026-08-15
28	Introduction to Electrodynamics	David J. Griffiths	4th	Pearson	2017	Physics	QC631.G75	978-0321856562	Book	Electrodynamics textbook	active	2026-08-15
29	Classical Mechanics	John R. Taylor	1st	University Science Books	2005	Physics	QA807.T39	978-1891389221	Book	Undergraduate classical mechanics	active	2026-08-15
30	Thermal Physics	Charles Kittel	2nd	W.H. Freeman	1980	Physics	QC311.K58	978-0716710882	Book	Thermodynamics and statistical mechanics	active	2026-08-15
31	Organic Chemistry	Paula Yurkanis Bruice	8th	Pearson	2020	Chemistry	QD251.3.B78	978-1260475678	Book	Organic chemistry textbook	active	2026-08-15
32	Physical Chemistry	Peter Atkins	11th	Oxford UP	2018	Chemistry	QD453.3.A85	978-0198769866	Book	Physical chemistry fundamentals	active	2026-08-15
33	Biochemistry	Jeremy M. Berg	9th	W.H. Freeman	2019	Biochemistry	QP514.2.B47	978-1319114671	Book	Biochemistry textbook	active	2026-08-15
34	Molecular Biology of the Cell	Bruce Alberts	6th	Garland Science	2014	Biology	QH581.2.A43	978-0815344322	Book	Cell biology reference	active	2026-08-15
35	Campbell Biology	Lisa Urry	12th	Pearson	2020	Biology	QH308.2.C36	978-0134093413	Book	General biology textbook	active	2026-08-15
36	Principles of Economics	N. Gregory Mankiw	9th	Cengage	2020	Economics	HB171.5.M36	978-1285165875	Book	Introductory economics textbook	active	2026-08-15
37	Microeconomics	Robert Pindyck	9th	Pearson	2017	Economics	HB172.P56	978-0134184241	Book	Intermediate microeconomics	active	2026-08-15
38	The Wealth of Nations	Adam Smith	1st	Bantam	2003	Economics	HB161.S65	978-0553585971	Book	Foundational economics text	active	2026-08-15
39	A Brief History of Time	Stephen Hawking	1st	Bantam	1998	Physics	QB981.H38	978-0553380163	Book	Popular science on cosmology	active	2026-08-15
40	The Selfish Gene	Richard Dawkins	1st	Oxford UP	2006	Biology	QH437.D39	978-0199291151	Book	Evolutionary biology classic	active	2026-08-15
41	On the Origin of Species	Charles Darwin	1st	Penguin	2003	Biology	QH365.O8 2003	978-0451529060	Book	Foundational evolutionary biology	active	2026-08-15
42	Silent Spring	Rachel Carson	1st	Mariner Books	2002	Environmental Science	QH545.P4 C37	978-0618249060	Book	Environmental science classic	active	2026-08-15
43	Fundamentals of Thermodynamics	Richard E. Sonntag	8th	Wiley	2013	Engineering	TJ265.S66	978-1118131992	Book	Engineering thermodynamics	active	2026-08-15
44	Fluid Mechanics	Frank M. White	8th	McGraw-Hill	2015	Engineering	TA357.W48	978-0073398273	Book	Engineering fluid mechanics	active	2026-08-15
45	Introduction to Robotics	John J. Craig	3rd	Pearson	2005	Engineering	TJ211.C67	978-0201543612	Book	Robotics fundamentals	active	2026-08-15
46	Engineering Mechanics: Dynamics	R.C. Hibbeler	14th	Pearson	2015	Engineering	TA352.H53	978-0133915389	Book	Dynamics textbook	active	2026-08-15
47	Digital Design	M. Morris Mano	6th	Pearson	2018	Engineering	TK7888.3.M36	978-0134549897	Book	Digital logic design	active	2026-08-15
48	Microelectronic Circuits	Adel S. Sedra	8th	Oxford UP	2020	Engineering	TK7867.S43	978-0190853549	Book	Analog and digital circuits	active	2026-08-15
49	Thermodynamics: An Engineering Approach	Yunus Cengel	9th	McGraw-Hill	2019	Engineering	TJ265.C46	978-0073398174	Book	Engineering thermodynamics	active	2026-08-15
50	Control Systems Engineering	Norman S. Nise	8th	Wiley	2019	Engineering	TJ213.N57	978-1119474227	Book	Control systems analysis and design	active	2026-08-15
51	The Art of Electronics	Paul Horowitz	3rd	Cambridge UP	2015	Engineering	TK7815.H67	978-0521809269	Book	Practical electronics reference	active	2026-08-15
52	Signals and Systems	Alan V. Oppenheim	2nd	Pearson	1996	Engineering	TK5102.9.O66	978-0138147570	Book	Signals and systems fundamentals	active	2026-08-15
53	Introduction to Algorithms for Data Mining	Weiss	2nd	CRC Press	2020	Computer Science	QA76.9.D3 W45	978-0768091110	Book	Data mining algorithms	active	2026-08-15
54	Compilers: Principles Techniques and Tools	Alfred V. Aho	2nd	Addison-Wesley	2006	Computer Science	QA76.6.A37	978-0321486813	Book	Dragon book on compilers	active	2026-08-15
55	Computer Architecture: A Quantitative Approach	John L. Hennessy	6th	Morgan Kaufmann	2017	Computer Science	QA76.9.A73 H46	978-0128119051	Book	Computer architecture reference	active	2026-08-15
56	Programming Pearls	Jon Bentley	2nd	Addison-Wesley	1999	Computer Science	QA76.6.B45	978-0201657883	Book	Algorithmic problem solving	active	2026-08-15
57	The Mythical Man-Month	Frederick Brooks	1st	Addison-Wesley	1995	Software Engineering	QA76.6.B76	978-0201835953	Book	Software project management classic	active	2026-08-15
58	Code Complete	Steve McConnell	2nd	Microsoft Press	2004	Software Engineering	QA76.76.D47 M33	978-0735619678	Book	Practical software construction	active	2026-08-15
59	Refactoring	Martin Fowler	2nd	Addison-Wesley	2018	Software Engineering	QA76.76.R42 F69	978-0134757599	Book	Improving existing code	active	2026-08-15
60	The Art of Computer Programming	Donald E. Knuth	3rd	Addison-Wesley	1997	Computer Science	QA76.6.K64	978-0201896831	Book	Encyclopedic algorithms reference	active	2026-08-15
61	Concrete Mathematics	Ronald L. Graham	2nd	Addison-Wesley	1994	Mathematics	QA39.2.G73	978-0201558029	Book	Mathematical foundations for CS	active	2026-08-15
62	Networking	Andrew S. Tanenbaum	5th	Pearson	2010	Computer Science	TK5105.5.T36	978-0133594140	Book	Computer network textbook	active	2026-08-15
63	The Sociopath Next Door	Martha Stout	1st	Broadway Books	2005	Psychology	RC555.S76	978-0767915823	Book	Understanding antisocial personality	active	2026-08-15
64	Thinking Fast and Slow	Daniel Kahneman	1st	Farrar Straus	2013	Psychology	BF441.K34	978-0374533557	Book	Cognitive biases and decision making	active	2026-08-15
65	The Power of Habit	Charles Duhigg	1st	Random House	2014	Psychology	BF335.D85	978-0812981605	Book	Science of habit formation	active	2026-08-15
66	Sapiens: A Brief History of Humankind	Yuval Noah Harari	1st	Harper	2015	History	CB113.H37	978-0062316097	Book	Human history overview	active	2026-08-15
67	The Guns of August	Barbara Tuchman	1st	Ballantine	2004	History	D530.T83	978-0345476098	Book	World War I origins	active	2026-08-15
69	The Elements of Style	William Strunk Jr.	4th	Pearson	1999	Language	PE1408.S77	978-0205309023	Book	English writing style guide	active	2026-08-15
70	The Art of War	Sun Tzu	1st	Shambhala	2005	Philosophy	U101.S95	978-1590302255	Book	Ancient military strategy	active	2026-08-15
71	Meditations	Marcus Aurelius	1st	Penguin	2006	Philosophy	BD161.A8 2006	978-0140449334	Book	Stoic philosophy reflections	active	2026-08-15
72	Thus Spoke Zarathustra	Friedrich Nietzsche	1st	Penguin	1969	Philosophy	B3313.A4 1969	978-0140441185	Book	Nietzsche philosophical novel	active	2026-08-15
73	Sophie's World	Jostein Gaarder	1st	Farrar Straus	2007	Philosophy	BD21.G33	978-0374530716	Book	History of philosophy novel	active	2026-08-15
74	Atomic Habits	James Clear	1st	Penguin	2018	Psychology	BF335.C53	978-0735211292	Book	Small habits big results	active	2026-08-15
75	Educated	Tara Westover	1st	Random House	2018	Autobiography	CT3262.W47	978-0399590504	Book	Memoir of self-education	active	2026-08-15
76	The Alchemist	Paulo Coelho	1st	Harper	2014	Literature	PQ9698.13.O35 A45	978-0062315007	Book	Inspirational allegorical novel	active	2026-08-15
77	The Little Prince	Antoine de Saint-Exupéry	1st	Mariner Books	2000	Literature	PQ2637.A274 P48	978-0156012195	Book	Philosophical children's tale	active	2026-08-15
78	Crime and Punishment	Fyodor Dostoevsky	1st	Dover	2001	Literature	PG3326.P7 2001	978-0486415871	Book	Russian psychological novel	active	2026-08-15
79	Brave New World	Aldous Huxley	1st	Harper Perennial	2006	Literature	PR6015.U9 B7	978-0060850524	Book	Dystopian sci-fi classic	active	2026-08-15
80	Frankenstein	Mary Shelley	1st	Dover	1994	Literature	PR5397.F7	978-0486282114	Book	Gothic science fiction novel	active	2026-08-15
81	Dracula	Bram Stoker	1st	Dover	2000	Literature	PR6037.T617 D7	978-0486411095	Book	Gothic horror classic	active	2026-08-15
82	The Adventures of Huckleberry Finn	Mark Twain	1st	Dover	1994	Literature	PS1305.A1 1994	978-0486280615	Book	American adventure novel	active	2026-08-15
83	Wuthering Heights	Emily Brontë	1st	Penguin	2002	Literature	PR4172.W7	978-0141439556	Book	Victorian Gothic romance	active	2026-08-15
84	Jane Eyre	Charlotte Brontë	1st	Penguin	2003	Literature	PR4167.J3 2003	978-0142437209	Book	Victorian coming-of-age novel	active	2026-08-15
85	The Hobbit	J.R.R. Tolkien	1st	Mariner Books	2012	Literature	PR6039.O32 H6	978-0547928227	Book	Fantasy adventure classic	active	2026-08-15
86	Fahrenheit 451	Ray Bradbury	1st	Simon Schuster	2012	Literature	PS3503.R167 F3	978-1451673319	Book	Dystopian novel about censorship	active	2026-08-15
87	The Book Thief	Markus Zusak	1st	Knopf	2007	Literature	PZ7.Z83 B6	978-0375842207	Book	WWII historical fiction	active	2026-08-15
88	Life of Pi	Yann Martel	1st	Mariner Books	2003	Literature	PR9199.3.M3855 L54	978-0156027328	Book	Survival and faith novel	active	2026-08-15
89	The Kite Runner	Khaled Hosseini	1st	Riverhead	2004	Literature	PS3608.O832 K58	978-1594480003	Book	Afghan historical fiction	active	2026-08-15
90	Guns Germs and Steel	Jared Diamond	1st	W.W. Norton	2005	History	HM206.D53	978-0393317558	Book	Civilization development factors	active	2026-08-15
68	A People's History of the United States	Howard Zinn	1st	Harper Perennial	2015	History	E178.Z56	978-0062397348	Book	Alternative US history	archived	2026-08-15
92	Cosmos	Carl Sagan	1st	Ballantine	2013	Science	QB44.3.S24	978-0345539434	Book	Universe exploration popular science	active	2026-08-15
93	The Elegant Universe	Brian Greene	1st	W.W. Norton	2003	Physics	QC794.6.S85 G74	978-0393338102	Book	String theory popular science	active	2026-08-15
94	The Gene: An Intimate History	Siddhartha Mukherjee	1st	Scribner	2016	Biology	QH431.M95	978-1476733500	Book	History of genetics	active	2026-08-15
95	The Immortal Life of Henrietta Lacks	Rebecca Skloot	1st	Crown	2010	Biology	RC265.6.L35 S55	978-1400052189	Book	Medical ethics and cell research	active	2026-08-15
96	Outliers: The Story of Success	Malcolm Gladwell	1st	Little Brown	2008	Psychology	BF637.S8 G53	978-0316017930	Book	Success factors analysis	active	2026-08-15
97	Freakonomics	Steven Levitt	1st	Harper	2009	Economics	HB74.P8 L48	978-0061245138	Book	Economics of everyday things	active	2026-08-15
98	The Tipping Point	Malcolm Gladwell	1st	Little Brown	2002	Sociology	HM1033.G53	978-0316346627	Book	Sociological change theory	active	2026-08-15
99	Steve Jobs	Walter Isaacson	1th	Simon Schuster	2015	Biography	QA76.2.J63 I83	978-1501127625	Book	Steve Jobs biography	active	2026-08-15
100	Elon Musk	Ashlee Vance	1st	Ecco	2015	Biography	HC102.5.M88 V36	978-0062301253	Book	Elon Musk biography	active	2026-08-15
101	Long Walk to Freedom	Nelson Mandela	1st	Little Brown	1995	Autobiography	DT1974.M35	978-0316548182	Book	Nelson Mandela autobiography	active	2026-08-15
102	I Know Why the Caged Bird Sings	Maya Angelou	1st	Ballantine	2009	Autobiography	PS3551.N464 I2	978-0345514400	Book	Maya Angelou memoir	active	2026-08-15
103	The Diary of a Young Girl	Anne Frank	1st	Bantam	1997	Autobiography	DS134.5.F7 1997	978-0553577129	Book	Holocaust diary	active	2026-08-15
104	Digital Minimalism	Cal Newport	1st	Portfolio	2019	Technology	HM851.N49	978-0525536512	Book	Digital declutter strategies	active	2026-08-15
105	The Innovators	Walter Isaacson	1st	Simon Schuster	2014	Technology	HD9696.2.U6 I83	978-1476708706	Book	History of the digital revolution	active	2026-08-15
106	The Phoenix Project	Gene Kim	3rd	IT Revolution	2018	Software Engineering	HD30.2.K56	978-1942788294	Book	DevOps IT novel	active	2026-08-15
107	The Lean Startup	Eric Ries	1st	Crown Business	2011	Business	HD62.5.R54	978-0307887894	Book	Startup methodology	active	2026-08-15
108	Good to Great	Jim Collins	1st	Harper Business	2001	Business	HD57.C65	978-0066620992	Book	Business management study	active	2026-08-15
109	Zero to One	Peter Thiel	1st	Crown Business	2014	Business	HD62.5.T45	978-0804139298	Book	Startup philosophy	active	2026-08-15
110	Deep Work	Cal Newport	1st	Grand Central	2016	Psychology	BF323.D5 N49	978-1455586691	Book	Focused work strategies	active	2026-08-15
111	The 7 Habits of Highly Effective People	Stephen Covey	1st	Simon Schuster	2020	Self-Help	BJ1581.C66	978-1982137274	Book	Personal effectiveness guide	active	2026-08-15
112	How to Win Friends and Influence People	Dale Carnegie	1st	Pocket Books	1998	Self-Help	BJ1581.C37	978-0671027032	Book	Interpersonal skills classic	active	2026-08-15
91	A Short History of Nearly Everything	Bill Bryson	1st	Broadway	2004	Science	Q162.B88	978-0767908184	Book	Popular science overview	archived	2026-08-15
17	1984 asd	George Orwell	1st	Signet	1950	Literature	PR6029.R8 N6	978-0451524935	Book	Dystopian political fiction	active	2026-08-15
\.


--
-- Data for Name: borrowers; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.borrowers (borrower_id, user_id, id_number, department, borrower_status, phone_number) FROM stdin;
2	2	2023-0040	BSIS	active	\N
1	1		BS Information Systems	active	\N
15	15	SEED100-001	BSIT	active	\N
16	16	SEED100-002	BSBA	active	\N
17	17	SEED100-003	BSED	active	\N
18	18	SEED100-004	BEED	active	\N
19	19	SEED100-005	BSHM	active	\N
20	20	SEED100-006	BS Criminology	active	\N
21	21	SEED100-007	BSIT	active	\N
22	22	SEED100-008	BSBA	active	\N
23	23	SEED100-009	BSED	active	\N
24	24	SEED100-010	BEED	active	\N
25	25	SEED100-011	BSHM	active	\N
26	26	SEED100-012	BS Criminology	active	\N
\.


--
-- Data for Name: circulation_records; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.circulation_records (circulation_id, book_id, accession_id, borrower_id, processed_by, borrow_type, transaction_type, borrow_date, due_date, return_date, fine_amount, damage_notes, lost_flag, transaction_status, fine_paid) FROM stdin;
1	1	1	1	1	daily_circulation	borrow	2026-08-15	2026-08-15	2026-08-15	0.00	\N	f	returned	f
2	1	1	2	2	daily_circulation	borrow	2026-08-15	2026-08-15	2026-08-15	0.00	\N	f	returned	f
3	2	2	2	2	daily_circulation	borrow	2026-08-15	2026-08-15	2026-08-15	0.00	\N	f	returned	f
5	1	1	1	1	daily_circulation	borrow	2026-08-15	2026-08-15	2026-08-15	0.00	\N	f	returned	f
4	2	2	2	2	daily_circulation	borrow	2026-08-15	2026-08-15	2026-08-15	0.00	\N	f	returned	f
6	2	2	2	2	daily_circulation	borrow	2026-08-15	2026-08-15	2026-08-15	0.00	\N	f	returned	f
7	2	2	2	2	daily_circulation	borrow	2026-08-15	2026-08-15	2026-08-15	0.00	\N	f	returned	f
8	2	2	2	2	daily_circulation	borrow	2026-08-15	2026-08-15	2026-08-15	0.00	\N	f	returned	f
9	17	17	2	2	overnight	borrow	2026-08-15	2026-08-17	2026-08-15	0.00	\N	f	returned	f
11	39	39	2	1	overnight	borrow	2026-08-17	2026-08-19	2026-08-17	0.00	\N	f	returned	f
10	17	17	2	2	overnight	borrow	2026-08-15	2026-08-17	2026-08-17	0.00	\N	f	returned	f
12	17	17	2	2	daily_circulation	borrow	2026-08-17	2026-08-17	2026-08-17	0.00	\N	f	returned	f
13	17	17	2	1	overnight	borrow	2026-08-17	2026-08-19	2026-08-17	0.00	\N	f	returned	f
16	33	33	2	1	overnight	borrow	2026-08-17	2026-08-19	2026-08-17	0.00	\N	f	returned	f
14	39	39	2	1	overnight	borrow	2026-08-17	2026-08-19	2026-08-17	0.00	\N	f	returned	f
15	68	68	2	1	overnight	borrow	2026-08-17	2026-08-19	2026-08-17	0.00	\N	f	returned	f
17	17	17	2	2	daily_circulation	borrow	2026-08-17	2026-08-17	2026-08-17	0.00	\N	f	returned	f
19	39	39	1	1	overnight	borrow	2026-08-21	2026-09-20	\N	0.00	\N	f	active	f
21	17	17	1	1	overnight	borrow	2026-08-22	2026-09-21	2026-08-22	0.00	napunit yung page 3	f	returned	f
22	39	114	2	2	daily_circulation	borrow	2026-09-03	2026-09-03	2026-09-03	0.00	\N	f	returned	f
18	17	113	2	1	overnight	borrow	2026-08-17	2026-08-19	2026-09-03	150.00	\N	f	returned	f
24	17	17	2	1	overnight	borrow	2026-09-03	2026-09-05	\N	0.00	\N	f	active	f
23	39	114	1	1	overnight	borrow	2026-09-03	2026-10-03	2026-09-03	0.00	\N	f	returned	f
20	68	68	2	1	overnight	borrow	2026-08-22	2026-08-24	2026-09-05	120.00	\N	f	returned	f
25	39	114	2	1	overnight	borrow	2026-09-13	2026-09-15	\N	0.00	\N	f	active	f
126	4	4	15	1	daily_circulation	borrow	2026-09-01	2026-09-01	\N	0.00	\N	f	active	f
127	15	15	16	1	overnight	borrow	2026-09-06	2026-09-08	\N	0.00	\N	f	active	f
128	2	2	17	1	overnight	borrow	2026-09-08	2026-09-10	\N	0.00	\N	f	active	f
129	19	19	18	1	daily_circulation	borrow	2026-07-28	2026-07-28	2026-07-29	0.00	\N	f	returned	f
130	27	27	19	1	daily_circulation	borrow	2026-06-03	2026-06-03	2026-06-04	0.00	\N	f	returned	f
131	1	1	20	1	overnight	borrow	2026-07-30	2026-08-01	2026-08-01	0.00	\N	f	returned	f
132	2	2	21	1	daily_circulation	borrow	2026-09-08	2026-09-08	2026-09-09	0.00	\N	f	returned	f
133	50	50	22	1	daily_circulation	borrow	2026-09-13	2026-09-13	\N	0.00	\N	f	active	f
134	94	94	23	1	daily_circulation	borrow	2026-04-09	2026-04-09	2026-04-10	0.00	\N	f	returned	f
135	44	44	24	1	daily_circulation	borrow	2026-05-02	2026-05-02	2026-05-03	0.00	\N	f	returned	f
136	52	52	25	1	daily_circulation	borrow	2026-08-30	2026-08-30	\N	0.00	\N	f	overdue	f
137	4	4	26	1	daily_circulation	borrow	2026-05-06	2026-05-06	\N	0.00	\N	f	overdue	f
138	5	5	15	1	overnight	borrow	2026-09-11	2026-09-13	\N	0.00	\N	f	active	f
139	17	113	16	1	daily_circulation	borrow	2026-04-15	2026-04-15	\N	0.00	\N	f	overdue	f
140	5	5	17	1	overnight	borrow	2026-06-15	2026-06-17	2026-06-15	0.00	\N	f	returned	f
141	69	69	18	1	daily_circulation	borrow	2026-08-15	2026-08-15	2026-08-16	0.00	\N	f	returned	f
142	14	14	19	1	daily_circulation	borrow	2026-06-04	2026-06-04	2026-06-06	0.00	\N	f	returned	f
143	71	71	20	1	daily_circulation	borrow	2026-09-05	2026-09-05	2026-09-06	0.00	\N	f	returned	f
144	7	7	21	1	daily_circulation	borrow	2026-07-26	2026-07-26	2026-07-26	0.00	\N	f	returned	f
145	1	1	22	1	overnight	borrow	2026-09-02	2026-09-04	\N	0.00	\N	f	active	f
146	4	4	23	1	daily_circulation	borrow	2026-08-29	2026-08-29	\N	0.00	\N	f	active	f
147	5	5	24	1	overnight	borrow	2026-09-01	2026-10-01	\N	0.00	\N	f	active	f
148	5	5	25	1	daily_circulation	borrow	2026-07-08	2026-07-08	2026-07-09	0.00	\N	f	returned	f
149	13	13	26	1	overnight	borrow	2026-07-28	2026-08-27	2026-08-27	0.00	\N	f	returned	f
150	3	3	15	1	overnight	borrow	2026-06-29	2026-07-01	2026-07-01	0.00	\N	f	returned	f
151	4	4	16	1	daily_circulation	borrow	2026-09-12	2026-09-12	2026-09-14	0.00	\N	f	returned	f
152	82	82	17	1	daily_circulation	borrow	2026-09-09	2026-09-09	\N	0.00	\N	f	active	f
153	4	4	18	1	daily_circulation	borrow	2026-09-06	2026-09-06	2026-09-06	0.00	\N	f	returned	f
154	5	5	19	1	daily_circulation	borrow	2026-06-16	2026-06-16	2026-06-16	0.00	\N	f	returned	f
155	1	1	20	1	daily_circulation	borrow	2026-08-29	2026-08-29	\N	0.00	\N	f	active	f
156	4	4	21	1	daily_circulation	borrow	2026-06-09	2026-06-09	2026-06-09	0.00	\N	f	returned	f
157	75	75	22	1	daily_circulation	borrow	2026-04-27	2026-04-27	2026-04-28	0.00	\N	f	returned	f
158	18	18	23	1	daily_circulation	borrow	2026-05-26	2026-05-26	2026-05-26	0.00	\N	f	returned	f
159	17	17	24	1	daily_circulation	borrow	2026-08-17	2026-08-17	2026-08-18	0.00	\N	f	returned	f
160	56	56	25	1	daily_circulation	borrow	2026-06-17	2026-06-17	2026-06-17	0.00	\N	f	returned	f
161	54	54	26	1	daily_circulation	borrow	2026-09-09	2026-09-09	2026-09-11	0.00	\N	f	returned	f
162	1	1	15	1	daily_circulation	borrow	2026-04-25	2026-04-25	\N	0.00	\N	t	overdue	f
163	76	76	16	1	overnight	borrow	2026-08-08	2026-08-10	\N	0.00	\N	f	overdue	f
164	1	1	17	1	daily_circulation	borrow	2026-09-11	2026-09-11	\N	0.00	\N	f	active	f
165	17	113	18	1	daily_circulation	borrow	2026-05-17	2026-05-17	2026-05-19	0.00	\N	f	returned	f
166	45	45	19	1	overnight	borrow	2026-07-18	2026-07-20	2026-07-20	0.00	\N	f	returned	f
167	1	1	20	1	daily_circulation	borrow	2026-08-13	2026-08-13	\N	0.00	\N	f	overdue	f
168	4	4	21	1	daily_circulation	borrow	2026-07-24	2026-07-24	\N	0.00	\N	f	overdue	f
169	33	33	22	1	daily_circulation	borrow	2026-09-07	2026-09-07	2026-09-07	0.00	\N	f	returned	f
170	6	6	23	1	daily_circulation	borrow	2026-04-19	2026-04-19	2026-04-21	0.00	\N	f	returned	f
171	2	2	24	1	daily_circulation	borrow	2026-06-13	2026-06-13	2026-06-14	0.00	\N	f	returned	f
172	3	3	25	1	overnight	borrow	2026-09-04	2026-10-04	\N	0.00	\N	f	active	f
173	3	3	26	1	daily_circulation	borrow	2026-09-08	2026-09-08	\N	0.00	\N	f	active	f
174	11	11	15	1	overnight	borrow	2026-08-23	2026-08-25	2026-08-24	0.00	\N	f	returned	f
175	1	1	16	1	daily_circulation	borrow	2026-05-24	2026-05-24	\N	0.00	\N	f	overdue	f
176	61	61	17	1	daily_circulation	borrow	2026-04-14	2026-04-14	2026-04-16	0.00	\N	f	returned	f
177	45	45	18	1	overnight	borrow	2026-09-13	2026-09-15	2026-09-14	0.00	\N	f	returned	f
178	4	4	19	1	overnight	borrow	2026-07-30	2026-08-01	2026-07-31	0.00	\N	f	returned	f
179	51	51	20	1	overnight	borrow	2026-09-07	2026-09-09	\N	0.00	\N	f	active	f
180	23	23	21	1	daily_circulation	borrow	2026-09-01	2026-09-01	2026-09-02	0.00	\N	f	returned	f
181	5	5	22	1	overnight	borrow	2026-08-29	2026-08-31	\N	0.00	\N	f	active	f
182	1	1	23	1	daily_circulation	borrow	2026-05-18	2026-05-18	2026-05-19	0.00	\N	f	returned	f
183	7	7	24	1	overnight	borrow	2026-08-26	2026-09-25	\N	0.00	\N	f	overdue	f
184	75	75	25	1	daily_circulation	borrow	2026-04-09	2026-04-09	2026-04-10	0.00	\N	f	returned	f
185	2	2	26	1	daily_circulation	borrow	2026-08-13	2026-08-13	2026-08-14	0.00	\N	f	returned	f
186	32	32	15	1	daily_circulation	borrow	2026-05-10	2026-05-10	2026-05-10	0.00	\N	f	returned	f
187	1	1	16	1	daily_circulation	borrow	2026-09-10	2026-09-10	\N	0.00	\N	f	active	f
188	29	29	17	1	overnight	borrow	2026-06-21	2026-06-23	2026-06-22	0.00	\N	f	returned	f
189	90	90	18	1	daily_circulation	borrow	2026-08-29	2026-08-29	\N	0.00	\N	f	active	f
190	5	5	19	1	overnight	borrow	2026-08-05	2026-08-07	\N	0.00	\N	f	overdue	f
191	3	3	20	1	daily_circulation	borrow	2026-08-25	2026-08-25	\N	0.00	\N	f	active	f
192	13	13	21	1	daily_circulation	borrow	2026-07-06	2026-07-06	\N	0.00	\N	f	overdue	f
193	5	5	22	1	daily_circulation	borrow	2026-03-23	2026-03-23	2026-03-25	0.00	\N	f	returned	f
194	40	40	23	1	overnight	borrow	2026-08-26	2026-08-28	\N	0.00	\N	f	active	f
195	82	82	24	1	daily_circulation	borrow	2026-07-23	2026-07-23	2026-07-25	0.00	\N	f	returned	f
196	4	4	25	1	overnight	borrow	2026-05-08	2026-06-07	2026-05-21	0.00	\N	f	returned	f
197	5	5	26	1	daily_circulation	borrow	2026-08-26	2026-08-26	\N	0.00	\N	f	active	f
198	58	58	15	1	daily_circulation	borrow	2026-06-12	2026-06-12	2026-06-13	0.00	\N	f	returned	f
199	5	5	16	1	daily_circulation	borrow	2026-08-30	2026-08-30	\N	0.00	\N	f	active	f
200	69	69	17	1	daily_circulation	borrow	2026-08-13	2026-08-13	2026-08-15	0.00	\N	f	returned	f
201	1	1	18	1	daily_circulation	borrow	2026-07-17	2026-07-17	\N	0.00	\N	f	overdue	f
202	96	96	19	1	daily_circulation	borrow	2026-04-20	2026-04-20	2026-04-20	0.00	\N	f	returned	f
203	23	23	20	1	overnight	borrow	2026-06-02	2026-06-04	2026-06-03	0.00	\N	f	returned	f
204	5	5	21	1	daily_circulation	borrow	2026-03-25	2026-03-25	2026-03-25	0.00	\N	f	returned	f
205	1	1	22	1	daily_circulation	borrow	2026-09-09	2026-09-09	2026-09-09	0.00	\N	f	returned	f
206	1	1	23	1	daily_circulation	borrow	2026-07-19	2026-07-19	2026-07-21	0.00	\N	f	returned	f
207	80	80	24	1	daily_circulation	borrow	2026-09-03	2026-09-03	\N	0.00	\N	f	active	f
208	45	45	25	1	overnight	borrow	2026-06-17	2026-07-17	2026-06-24	0.00	\N	f	returned	f
209	50	50	26	1	overnight	borrow	2026-09-14	2026-10-14	2026-10-04	0.00	\N	f	returned	f
210	4	4	15	1	overnight	borrow	2026-06-01	2026-06-03	2026-06-03	0.00	\N	f	returned	f
211	100	100	16	1	overnight	borrow	2026-04-15	2026-04-17	2026-04-16	0.00	\N	f	returned	f
212	4	4	17	1	daily_circulation	borrow	2026-07-23	2026-07-23	2026-07-23	0.00	\N	f	returned	f
213	69	69	18	1	daily_circulation	borrow	2026-09-03	2026-09-03	\N	0.00	\N	f	active	f
214	17	115	19	1	daily_circulation	borrow	2026-09-08	2026-09-08	\N	0.00	\N	f	active	f
215	43	43	20	1	daily_circulation	borrow	2026-07-14	2026-07-14	2026-07-15	0.00	\N	f	returned	f
216	3	3	21	1	overnight	borrow	2026-06-26	2026-06-28	2026-06-27	0.00	\N	f	returned	f
217	65	65	22	1	overnight	borrow	2026-04-05	2026-04-07	2026-04-05	0.00	\N	f	returned	f
218	4	4	23	1	overnight	borrow	2026-08-25	2026-08-27	\N	0.00	\N	f	active	f
219	2	2	24	1	overnight	borrow	2026-07-04	2026-08-03	\N	0.00	\N	f	overdue	f
220	77	77	25	1	daily_circulation	borrow	2026-07-05	2026-07-05	2026-07-06	0.00	\N	f	returned	f
221	73	73	26	1	daily_circulation	borrow	2026-05-28	2026-05-28	2026-05-29	0.00	\N	f	returned	f
222	4	4	15	1	daily_circulation	borrow	2026-09-04	2026-09-04	\N	0.00	\N	f	active	f
223	45	45	16	1	overnight	borrow	2026-06-11	2026-06-13	2026-06-13	0.00	\N	f	returned	f
224	1	1	17	1	daily_circulation	borrow	2026-08-25	2026-08-25	2026-08-25	0.00	\N	f	returned	f
225	100	100	18	1	daily_circulation	borrow	2026-08-27	2026-08-27	\N	0.00	\N	f	active	f
\.


--
-- Data for Name: departments; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.departments (department_id, name, dept_type) FROM stdin;
1	BSIS	program
2	BSN	program
3	BACOMM	program
\.


--
-- Data for Name: inventory_sessions; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.inventory_sessions (session_id, librarian_id, total_books, scanned_count, session_status, started_at, ended_at) FROM stdin;
1	1	1	1	completed	2026-08-09 00:00:00	2026-08-09 00:00:00
2	1	1	1	cancelled	2026-08-09 00:00:00	2026-08-10 00:00:00
3	1	1	1	completed	2026-08-15 00:00:00	2026-08-15 00:00:00
\.


--
-- Data for Name: inventory_status; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.inventory_status (inventory_id, accession_id, inventory_state, inventory_type, checked_by, last_checked_date, session_id, notes) FROM stdin;
1	1	lost	annual_physical	\N	2026-08-24	\N	\N
32	2	available	realtime_scan	1	2026-09-14	\N	SEED100
33	3	available	realtime_scan	1	2026-09-14	\N	SEED100
34	4	available	realtime_scan	1	2026-09-14	\N	SEED100
35	5	available	realtime_scan	1	2026-09-14	\N	SEED100
36	6	available	realtime_scan	1	2026-09-14	\N	SEED100
37	7	available	realtime_scan	1	2026-09-14	\N	SEED100
38	8	available	realtime_scan	1	2026-09-14	\N	SEED100
39	9	available	realtime_scan	1	2026-09-14	\N	SEED100
40	10	available	realtime_scan	1	2026-09-14	\N	SEED100
41	11	available	realtime_scan	1	2026-09-14	\N	SEED100
42	12	available	realtime_scan	1	2026-09-14	\N	SEED100
43	13	available	realtime_scan	1	2026-09-14	\N	SEED100
44	14	available	realtime_scan	1	2026-09-14	\N	SEED100
45	15	available	realtime_scan	1	2026-09-14	\N	SEED100
46	16	available	realtime_scan	1	2026-09-14	\N	SEED100
47	17	available	realtime_scan	1	2026-09-14	\N	SEED100
48	18	borrowed	realtime_scan	1	2026-09-14	\N	SEED100
49	19	borrowed	realtime_scan	1	2026-09-14	\N	SEED100
50	20	borrowed	realtime_scan	1	2026-09-14	\N	SEED100
51	21	borrowed	realtime_scan	1	2026-09-14	\N	SEED100
52	22	borrowed	realtime_scan	1	2026-09-14	\N	SEED100
53	23	borrowed	realtime_scan	1	2026-09-14	\N	SEED100
54	24	borrowed	realtime_scan	1	2026-09-14	\N	SEED100
55	25	borrowed	realtime_scan	1	2026-09-14	\N	SEED100
56	26	damaged	realtime_scan	1	2026-09-14	\N	SEED100
57	27	damaged	realtime_scan	1	2026-09-14	\N	SEED100
58	28	missing	realtime_scan	1	2026-09-14	\N	SEED100
59	29	missing	realtime_scan	1	2026-09-14	\N	SEED100
60	30	lost	realtime_scan	1	2026-09-14	\N	SEED100
61	31	lost	realtime_scan	1	2026-09-14	\N	SEED100
\.


--
-- Data for Name: library_settings; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.library_settings (setting_key, setting_value, description, updated_at, updated_by) FROM stdin;
MAX_BORROW_LIMIT_STUDENT	3	Max active loans for students	2026-09-05 16:49:07.874882	\N
MAX_BORROW_LIMIT_FACULTY	5	Max active loans for faculty	2026-09-05 16:49:07.874882	\N
OVERNIGHT_DUE_DAYS_STUDENT	2	Overnight loan due days for students	2026-09-05 16:49:07.874882	\N
OVERNIGHT_DUE_DAYS_FACULTY	30	Overnight loan due days for faculty	2026-09-05 16:49:07.874882	\N
DAILY_CIRCULATION_DUE_DAYS	0	Daily circulation due days (0 = same day)	2026-09-05 16:49:07.874882	\N
OVERDUE_FINE_PER_DAY	10.0	Overdue fine in pesos per day	2026-09-05 16:49:07.874882	\N
OVERDUE_GRACE_DAYS	0	Grace days before fines accrue	2026-09-05 16:49:07.874882	\N
RESERVATION_CLAIM_DAYS	2	Days to claim an allocated reservation	2026-09-05 16:49:07.874882	\N
DUE_SOON_NOTIFY_DAYS	2	Days before due date to send due-soon reminders	2026-09-05 16:49:07.874882	\N
\.


--
-- Data for Name: notification_log; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.notification_log (notification_id, recipient_id, message, notif_type, related_reference, date_sent, is_read) FROM stdin;
26	2	Overdue fine of ₱120.00 assessed for copy ACC-0066. Please settle at the desk.	fine	20	2026-09-05 18:27:45.619443	t
1	2	Your reserved book is ready. Claim within 2 days.	hold_ready	1	2026-08-15 10:08:19.07764	t
2	2	A reserved copy of "Introduction to Computing" is ready for pickup.	hold_ready	2	2026-08-15 10:11:30.098705	t
3	2	Your reserved book is ready. Claim within 2 days.	hold_ready	2	2026-08-15 10:13:24.719816	t
10	2	Your reserved book is ready. Claim within 2 days.	hold_ready	7	2026-08-17 09:23:41.518319	t
11	2	Your reserved book is ready. Claim within 2 days.	hold_ready	8	2026-08-17 10:24:41.749745	t
12	2	Your reserved book is ready. Claim within 2 days.	hold_ready	9	2026-08-17 10:27:17.047764	t
13	2	Your reserved book is ready. Claim within 2 days.	hold_ready	10	2026-08-17 10:28:28.942016	t
14	2	Your reserved book is ready. Claim within 2 days.	hold_ready	11	2026-08-17 10:29:09.743339	t
15	2	Your reserved book is ready. Claim within 2 days.	hold_ready	12	2026-08-17 10:32:32.965379	t
17	2	Your reserved book is ready. Claim within 2 days.	hold_ready	14	2026-08-22 09:18:45.213963	t
21	2	Your reserved book is ready. Claim within 2 days.	hold_ready	21	2026-09-03 20:37:43.417832	t
22	2	A reserved copy of "A Brief History of Time" is ready for pickup.	hold_ready	20	2026-09-03 20:47:34.439299	t
23	2	Overdue: "A People's History of the United States" was due 2026-08-24. Please return it to avoid further fines.	overdue_reminder	20	2026-09-05 16:49:29.580561	t
24	2	Reminder: "1984" is due 2026-09-05 (in 0 day(s)).	due_soon	24	2026-09-05 16:49:29.60167	t
25	2	You returned copy ACC-0066. Overdue fine: ₱120.00.	return	20	2026-09-05 18:27:45.615096	t
4	1	A reserved copy of "Computer Programming 1" is ready for pickup.	hold_ready	3	2026-08-15 11:13:02.12836	t
5	1	Your reserved book is ready. Claim within 2 days.	hold_ready	3	2026-08-15 11:13:07.041978	t
6	1	A reserved copy of "Computer Programming 1" is ready for pickup.	hold_ready	4	2026-08-15 11:14:23.000301	t
7	1	Your reserved book is ready. Claim within 2 days.	hold_ready	4	2026-08-15 11:14:28.233622	t
8	1	A reserved copy of "Computer Programming 1" is ready for pickup.	hold_ready	6	2026-08-15 13:20:04.138344	t
9	1	Your reserved book is ready. Claim within 2 days.	hold_ready	6	2026-08-15 13:20:18.260268	t
16	1	Your reserved book is ready. Claim within 2 days.	hold_ready	13	2026-08-21 13:35:27.23348	t
18	1	Your reserved book is ready. Claim within 2 days.	hold_ready	15	2026-08-22 13:43:34.255105	t
19	1	A reserved copy of "A Brief History of Time" is ready for pickup.	hold_ready	17	2026-09-03 17:18:35.407798	t
20	1	Your reserved book is ready. Claim within 2 days.	hold_ready	17	2026-09-03 20:35:54.294667	t
29	1	Reservation #19 expired/cancelled.	reservation	19	2026-09-13 13:38:48.570086	t
37	1	Reminder: "A Brief History of Time" is due 2026-09-20 (in 2 day(s)).	due_soon	19	2026-09-18 14:10:46.845243	t
27	2	Overdue: "1984" was due 2026-09-05. Please return it to avoid further fines.	overdue_reminder	24	2026-09-08 13:54:14.136604	t
28	2	Overdue: "1984" was due 2026-09-05. Please return it to avoid further fines.	overdue_reminder	24	2026-09-13 13:35:13.736597	t
30	2	Reservation #22 expired/cancelled.	reservation	22	2026-09-13 13:42:07.600667	t
31	2	Your reserved book is ready. Claim within 2 days.	hold_ready	20	2026-09-13 13:52:40.063344	t
32	2	Reservation #20 allocated. Claim by Sep 15, 2026.	reservation	20	2026-09-13 13:52:40.064585	t
33	2	Reservation #20 claimed. Book due 2026-09-15.	reservation	20	2026-09-13 14:07:31.967081	t
34	2	Reminder: "A Brief History of Time" is due 2026-09-15 (in 2 day(s)).	due_soon	25	2026-09-13 14:08:46.04098	t
35	2	Overdue: "1984" was due 2026-09-05. Please return it to avoid further fines.	overdue_reminder	24	2026-09-18 14:10:21.086893	t
36	2	Overdue: "A Brief History of Time" was due 2026-09-15. Please return it to avoid further fines.	overdue_reminder	25	2026-09-18 14:10:21.10682	t
38	1	Overdue: "A Brief History of Time" was due 2026-09-20. Please return it to avoid further fines.	overdue_reminder	19	2026-09-21 08:19:34.346565	f
39	2	Overdue: "1984" was due 2026-09-05. Please return it to avoid further fines.	overdue_reminder	24	2026-09-21 08:32:04.249356	f
40	2	Overdue: "A Brief History of Time" was due 2026-09-15. Please return it to avoid further fines.	overdue_reminder	25	2026-09-21 08:32:04.251721	f
41	1	Overdue: "A Brief History of Time" was due 2026-09-20. Please return it to avoid further fines.	overdue_reminder	19	2026-09-24 09:29:06.769916	f
42	2	Overdue: "1984 asd" was due 2026-09-05. Please return it to avoid further fines.	overdue_reminder	24	2026-09-26 09:03:18.444063	f
43	2	Overdue: "A Brief History of Time" was due 2026-09-15. Please return it to avoid further fines.	overdue_reminder	25	2026-09-26 09:03:18.453631	f
44	1	Overdue: "A Brief History of Time" was due 2026-09-20. Please return it to avoid further fines.	overdue_reminder	19	2026-09-26 09:04:34.868932	f
\.


--
-- Data for Name: procurement_log; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.procurement_log (procurement_id, request_id, order_status, order_date, date_received, book_id, remarks) FROM stdin;
1	1	delivered	2026-08-15	\N	\N	\N
\.


--
-- Data for Name: request_records; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.request_records (request_id, requester_id, book_title, author, matched_book_id, request_status, request_date, reviewed_by, review_date, remarks) FROM stdin;
1	1	Introductin to Computing	\N	\N	approved	2026-08-15 06:49:58.592281	1	2026-08-15 06:50:17.087687	\N
2	2	hey	\N	\N	rejected	2026-08-15 13:48:47.595214	1	2026-08-23 20:58:56.626017	Just because
\.


--
-- Data for Name: reservation_queue; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.reservation_queue (reservation_id, book_id, borrower_id, queue_position, request_date, reservation_status, claim_deadline) FROM stdin;
1	1	2	1	2026-08-15 10:07:10.210054	claimed	2026-08-17 10:08:19.069619
2	1	2	2	2026-08-15 10:10:29.392192	claimed	2026-08-17 10:13:24.717539
3	2	1	1	2026-08-15 11:10:04.583977	claimed	2026-08-17 11:13:07.036322
4	2	1	2	2026-08-15 11:13:43.019241	claimed	2026-08-17 11:14:28.227968
5	2	1	3	2026-08-15 13:16:53.446902	expired	\N
6	2	1	4	2026-08-15 13:19:33.553045	claimed	2026-08-17 13:20:18.257582
7	39	2	1	2026-08-17 09:23:14.621817	claimed	2026-08-19 09:23:41.50793
8	17	2	1	2026-08-17 10:24:24.581208	claimed	2026-08-19 10:24:41.744795
9	39	2	2	2026-08-17 10:26:54.056931	claimed	2026-08-19 10:27:17.043314
10	68	2	1	2026-08-17 10:28:03.135063	claimed	2026-08-19 10:28:28.937414
11	33	2	1	2026-08-17 10:28:57.70891	claimed	2026-08-19 10:29:09.738736
12	17	2	2	2026-08-17 10:32:06.410308	claimed	2026-08-19 10:32:32.959922
13	39	1	3	2026-08-21 13:34:36.517463	claimed	2026-08-23 13:35:27.21757
14	68	2	2	2026-08-22 09:18:17.918945	claimed	2026-08-24 09:18:45.205201
15	17	1	3	2026-08-22 13:41:32.853084	claimed	2026-08-24 13:43:34.242113
16	39	1	4	2026-09-03 17:04:55.818497	expired	\N
18	39	2	6	2026-09-03 17:14:05.776923	expired	\N
17	39	1	5	2026-09-03 17:13:18.016232	claimed	2026-09-05 20:35:54.289746
21	17	2	4	2026-09-03 20:37:30.708316	claimed	2026-09-05 20:37:43.41442
19	79	1	1	2026-09-03 20:34:30.623567	expired	\N
22	17	2	5	2026-09-03 20:40:27.461335	expired	\N
20	39	2	7	2026-09-03 20:35:43.740977	claimed	2026-09-15 13:52:40.060423
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

COPY public.user_accounts (user_id, email, oauth_sub, full_name, role_id, account_status, created_at) FROM stdin;
2	justin.batlangao@mcst.edu.ph	108913924297114452491	JUSTIN BATLANGAO	1	active	2026-08-15 08:31:50.185274
1	glennpatrick.darriguez@mcst.edu.ph	116655272240063205223	GLENN PATRICK DARRIGUEZ	4	active	2026-08-09 20:35:08.871445
15	seed100_01@mcst.edu.ph	seed100_oauth_01	Alex Santos	1	active	2026-09-14 08:49:42.491683
16	seed100_02@mcst.edu.ph	seed100_oauth_02	Maria Bautista	1	active	2026-09-14 08:49:42.491683
17	seed100_03@mcst.edu.ph	seed100_oauth_03	Jose Mendoza	1	active	2026-09-14 08:49:42.491683
18	seed100_04@mcst.edu.ph	seed100_oauth_04	Ana Aquino	1	active	2026-09-14 08:49:42.491683
19	seed100_05@mcst.edu.ph	seed100_oauth_05	Mark Santos	1	active	2026-09-14 08:49:42.491683
20	seed100_06@mcst.edu.ph	seed100_oauth_06	Liza Bautista	1	active	2026-09-14 08:49:42.491683
21	seed100_07@mcst.edu.ph	seed100_oauth_07	John Mendoza	1	active	2026-09-14 08:49:42.491683
22	seed100_08@mcst.edu.ph	seed100_oauth_08	Rosa Aquino	1	active	2026-09-14 08:49:42.491683
23	seed100_09@mcst.edu.ph	seed100_oauth_09	Paolo Santos	1	active	2026-09-14 08:49:42.491683
24	seed100_10@mcst.edu.ph	seed100_oauth_10	Nina Bautista	2	active	2026-09-14 08:49:42.491683
25	seed100_11@mcst.edu.ph	seed100_oauth_11	Carlos Mendoza	2	active	2026-09-14 08:49:42.491683
26	seed100_12@mcst.edu.ph	seed100_oauth_12	Ella Aquino	2	active	2026-09-14 08:49:42.491683
\.


--
-- Data for Name: user_favorites; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.user_favorites (favorite_id, user_id, book_id, created_at) FROM stdin;
\.


--
-- Data for Name: user_sessions; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.user_sessions (session_id, user_id, login_at, logout_at, last_seen, ip_address, user_agent) FROM stdin;
\.


--
-- Name: accession_log_accession_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.accession_log_accession_id_seq', 115, true);


--
-- Name: analytics_cache_cache_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.analytics_cache_cache_id_seq', 49, true);


--
-- Name: audit_trail_log_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.audit_trail_log_id_seq', 204, true);


--
-- Name: backup_log_backup_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.backup_log_backup_id_seq', 8, true);


--
-- Name: book_catalog_book_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.book_catalog_book_id_seq', 112, true);


--
-- Name: borrowers_borrower_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.borrowers_borrower_id_seq', 26, true);


--
-- Name: circulation_records_circulation_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.circulation_records_circulation_id_seq', 225, true);


--
-- Name: departments_department_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.departments_department_id_seq', 27, true);


--
-- Name: inventory_sessions_session_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.inventory_sessions_session_id_seq', 3, true);


--
-- Name: inventory_status_inventory_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.inventory_status_inventory_id_seq', 61, true);


--
-- Name: notification_log_notification_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.notification_log_notification_id_seq', 44, true);


--
-- Name: procurement_log_procurement_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.procurement_log_procurement_id_seq', 1, true);


--
-- Name: request_records_request_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.request_records_request_id_seq', 2, true);


--
-- Name: reservation_queue_reservation_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.reservation_queue_reservation_id_seq', 22, true);


--
-- Name: roles_role_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.roles_role_id_seq', 660, true);


--
-- Name: user_accounts_user_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.user_accounts_user_id_seq', 26, true);


--
-- Name: user_favorites_favorite_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.user_favorites_favorite_id_seq', 1, false);


--
-- Name: user_sessions_session_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.user_sessions_session_id_seq', 1, false);


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
-- Name: user_sessions user_sessions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_sessions
    ADD CONSTRAINT user_sessions_pkey PRIMARY KEY (session_id);


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
-- Name: inventory_sessions inventory_sessions_librarian_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.inventory_sessions
    ADD CONSTRAINT inventory_sessions_librarian_id_fkey FOREIGN KEY (librarian_id) REFERENCES public.user_accounts(user_id);


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
-- Name: user_accounts user_accounts_role_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_accounts
    ADD CONSTRAINT user_accounts_role_id_fkey FOREIGN KEY (role_id) REFERENCES public.roles(role_id);


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
-- Name: user_sessions user_sessions_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_sessions
    ADD CONSTRAINT user_sessions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.user_accounts(user_id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

\unrestrict xbzw0hMN6zc8yfCBBgipDb1zDf8mV05HfkEhMYs4HjO1fmc88Sp0fPW9uQwiRgg

