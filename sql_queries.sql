


SELECT COUNT(*) AS total_rows FROM luxury_housing_sales;


SELECT
    SUM(CASE WHEN Ticket_Price_Cr IS NULL THEN 1 ELSE 0 END) AS null_price,
    SUM(CASE WHEN Amenity_Score   IS NULL THEN 1 ELSE 0 END) AS null_amenity,
    SUM(CASE WHEN Unit_Size_Sqft  IS NULL THEN 1 ELSE 0 END) AS null_size,
    SUM(CASE WHEN Micro_Market    IS NULL THEN 1 ELSE 0 END) AS null_market
FROM luxury_housing_sales;


SELECT Transaction_Type, COUNT(*) AS count
FROM luxury_housing_sales
GROUP BY Transaction_Type
ORDER BY count DESC;


SELECT
    Developer_Name,
    COUNT(*)                             AS total_units,
    ROUND(SUM(Ticket_Price_Cr), 2)       AS total_revenue_cr,
    ROUND(AVG(Ticket_Price_Cr), 2)       AS avg_ticket_cr,
    ROUND(AVG(Price_per_Sqft), 0)        AS avg_price_psf
FROM luxury_housing_sales
GROUP BY Developer_Name
ORDER BY total_revenue_cr DESC
LIMIT 10;


SELECT
    Purchase_Quarter_Label              AS quarter,
    COUNT(*)                            AS total_units,
    SUM(Booking_Flag)                   AS primary_bookings,
    ROUND(100.0 * SUM(Booking_Flag) / COUNT(*), 1) AS booking_pct,
    ROUND(AVG(Ticket_Price_Cr), 2)      AS avg_ticket_cr
FROM luxury_housing_sales
GROUP BY Purchase_Quarter_Label
ORDER BY Purchase_Quarter_Label;


SELECT
    Micro_Market,
    COUNT(*)                            AS total_units,
    ROUND(AVG(Ticket_Price_Cr), 2)      AS avg_ticket_cr,
    ROUND(AVG(Price_per_Sqft), 0)       AS avg_psf,
    ROUND(AVG(Amenity_Score), 2)        AS avg_amenity
FROM luxury_housing_sales
GROUP BY Micro_Market
ORDER BY total_units DESC
LIMIT 10;


SELECT
    Configuration,
    COUNT(*)                            AS total_units,
    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM luxury_housing_sales), 1) AS pct_share,
    ROUND(AVG(Ticket_Price_Cr), 2)      AS avg_ticket_cr
FROM luxury_housing_sales
GROUP BY Configuration
ORDER BY total_units DESC;


SELECT
    Sales_Channel,
    COUNT(*)                            AS total_inquiries,
    SUM(Booking_Flag)                   AS bookings,
    ROUND(100.0 * SUM(Booking_Flag) / COUNT(*), 1) AS conversion_pct,
    ROUND(AVG(Ticket_Price_Cr), 2)      AS avg_ticket_cr
FROM luxury_housing_sales
GROUP BY Sales_Channel
ORDER BY conversion_pct DESC;


SELECT
    Amenity_Band,
    COUNT(*)                            AS total_units,
    SUM(Booking_Flag)                   AS bookings,
    ROUND(100.0 * SUM(Booking_Flag) / COUNT(*), 1) AS booking_pct,
    ROUND(AVG(Amenity_Score), 2)        AS avg_amenity_score
FROM luxury_housing_sales
GROUP BY Amenity_Band
ORDER BY avg_amenity_score;


SELECT
    Possession_Status,
    Buyer_Type,
    COUNT(*)                            AS count,
    ROUND(AVG(Ticket_Price_Cr), 2)      AS avg_ticket_cr
FROM luxury_housing_sales
GROUP BY Possession_Status, Buyer_Type
ORDER BY Possession_Status, count DESC;


SELECT
    Micro_Market,
    SUM(NRI_Flag)                       AS nri_buyers,
    COUNT(*)                            AS total,
    ROUND(100.0 * SUM(NRI_Flag) / COUNT(*), 1) AS nri_pct
FROM luxury_housing_sales
GROUP BY Micro_Market
ORDER BY nri_pct DESC
LIMIT 10;


SELECT
    Developer_Name,
    Purchase_Quarter_Label,
    COUNT(*)                            AS units,
    ROUND(SUM(Ticket_Price_Cr), 2)      AS total_revenue_cr
FROM luxury_housing_sales
GROUP BY Developer_Name, Purchase_Quarter_Label
ORDER BY Developer_Name, Purchase_Quarter_Label;
