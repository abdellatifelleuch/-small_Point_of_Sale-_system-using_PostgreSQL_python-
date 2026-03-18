-- ===============================
-- 1. ENUM TYPE FOR CATEGORY
-- ===============================
CREATE TYPE category_enum AS ENUM ('piece', 'kg', 'm');

-- ===============================
-- 2. PRODUCT TABLE
-- ===============================
CREATE TABLE produit (
    bar_code VARCHAR(50) PRIMARY KEY,
    designation TEXT NOT NULL,
    marque TEXT NOT NULL,
    category category_enum NOT NULL,
    prix_achat NUMERIC(10, 2) NOT NULL CHECK (prix_achat >= 0),
    prix_vende NUMERIC(10, 2) NOT NULL CHECK (prix_vende > 0),
    img_path TEXT,
    quantity INTEGER NOT NULL DEFAULT 0 CHECK (quantity >= 0)
);

-- ===============================
-- 3. PRICE VALIDATION TRIGGER
-- ===============================
CREATE OR REPLACE FUNCTION verif_prix_finalle()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.prix_vende <= NEW.prix_achat THEN
        RAISE EXCEPTION 'Le prix de vente (%) doit être supérieur au prix d''achat (%)',
            NEW.prix_vende, NEW.prix_achat;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER verif_prix_trigger
BEFORE INSERT OR UPDATE ON produit
FOR EACH ROW
EXECUTE FUNCTION verif_prix_finalle();

-- ===============================
-- 4. PRODUCT VIEW
-- ===============================
CREATE OR REPLACE VIEW vue_produit_en_temps_reel AS
SELECT 
    bar_code,
    designation,
    marque,
    category,
    prix_achat,
    prix_vende,
    img_path,
    quantity
FROM produit;

-- ===============================
-- 5. HISTORY TABLE
-- ===============================
CREATE TABLE history (
    id SERIAL PRIMARY KEY,
    bar_code VARCHAR(50),
    action_type TEXT NOT NULL CHECK (action_type IN ('insert', 'update', 'purchase')),
    old_quantity INTEGER,
    new_quantity INTEGER,
    prix_achat NUMERIC(10, 2),
    prix_vende NUMERIC(10, 2),
    change_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    remarks TEXT
);

-- ===============================
-- 6. TRIGGER FUNCTION FOR produit
-- ===============================
CREATE OR REPLACE FUNCTION log_product_changes()
RETURNS TRIGGER AS $$
DECLARE
    action TEXT;
    remarque TEXT := '';
BEGIN
    IF TG_OP = 'INSERT' THEN
        action := 'insert';
        remarque := 'Nouveau produit ajouté';
        INSERT INTO history (
            bar_code, action_type, new_quantity, prix_achat, prix_vende, remarks
        ) VALUES (
            NEW.bar_code, action, NEW.quantity, NEW.prix_achat, NEW.prix_vende, remarque
        );

    ELSIF TG_OP = 'UPDATE' THEN
        IF NEW.quantity <> OLD.quantity THEN
            action := 'purchase';
            remarque := 'Quantité modifiée';
        ELSE
            action := 'update';
            remarque := 'Produit modifié';
        END IF;

        IF NEW.prix_achat <> OLD.prix_achat THEN
            remarque := remarque || ' | Prix achat changé';
        END IF;

        IF NEW.prix_vende <> OLD.prix_vende THEN
            remarque := remarque || ' | Prix vente changé';
        END IF;

        INSERT INTO history (
            bar_code,
            action_type,
            old_quantity, new_quantity,
            prix_achat, prix_vende,
            remarks
        ) VALUES (
            NEW.bar_code,
            action,
            OLD.quantity, NEW.quantity,
            NEW.prix_achat, NEW.prix_vende,
            remarque
        );
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER produit_history_trigger
AFTER INSERT OR UPDATE ON produit
FOR EACH ROW
EXECUTE FUNCTION log_product_changes();

-- ===============================
-- 7. SALES TABLE
-- ===============================
CREATE TABLE ventes (
    id SERIAL PRIMARY KEY,
    bar_code VARCHAR(50) REFERENCES produit(bar_code),
    designation TEXT NOT NULL,
    quantity_sold INTEGER NOT NULL CHECK (quantity_sold > 0),
    prix_vende NUMERIC(10, 2) NOT NULL CHECK (prix_vende >= 0),
    total_vente NUMERIC(10, 2) GENERATED ALWAYS AS (quantity_sold * prix_vende) STORED,
    date_vente TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ===============================
-- 8. TRIGGER FUNCTION FOR ventes
-- ===============================
CREATE OR REPLACE FUNCTION log_ventes_to_history()
RETURNS TRIGGER AS $$
DECLARE
    old_qty INTEGER;
    new_qty INTEGER;
    remarque TEXT := 'Vente enregistrée depuis la table ventes';
BEGIN
    SELECT quantity + NEW.quantity_sold INTO old_qty
    FROM produit WHERE bar_code = NEW.bar_code;

    SELECT quantity INTO new_qty
    FROM produit WHERE bar_code = NEW.bar_code;

    INSERT INTO history (
        bar_code,
        action_type,
        old_quantity,
        new_quantity,
        prix_achat,
        prix_vende,
        remarks
    )
    SELECT 
        NEW.bar_code,
        'purchase',
        old_qty,
        new_qty,
        p.prix_achat,
        NEW.ventes.prix_vende,
        remarque
    FROM produit p
    WHERE p.bar_code = NEW.bar_code;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER ventes_trigger
AFTER INSERT ON ventes
FOR EACH ROW
EXECUTE FUNCTION log_ventes_to_history();




