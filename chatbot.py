# import psycopg2
# from flask import Flask, request, render_template, jsonify
# from datetime import datetime, timedelta
# import pandas as pd
# import re

# # Database connection
# def get_db_connection():
#     try:
#         conn = psycopg2.connect(
#             host="ep-steep-smoke-a8y63192-pooler.eastus2.azure.neon.tech",
#             database="neondb",
#             user="neondb_owner",
#             password="npg_KB7gQX9tyron",
#             port="5432"
#         )
#         return conn
#     except Exception as e:
#         print(f"Error: {e}")
#         return None

# # Helper function for sell-out days
# def calculate_days_to_sell_out(sales_qty, purchase_qty, days_since):
#     if sales_qty == 0 or purchase_qty == 0:
#         return "N/A"
#     remaining = purchase_qty - sales_qty
#     if remaining <= 0:
#         return "Sold out"
#     daily_rate = sales_qty / days_since
#     return round(remaining / daily_rate) if daily_rate > 0 else "N/A"

# # Helper function to extract category from question
# def extract_category(question):
#     words = question.lower().split()
#     try:
#         if "in" in words:
#             idx = words.index("in") + 1
#             category_words = []
#             for i in range(idx, len(words)):
#                 if words[i] in ["daily", "historical", "trend"]:
#                     break
#                 category_words.append(words[i])
#             return " ".join(category_words).capitalize()
#         elif "for" in words:
#             idx = words.index("for") + 1
#             category_words = []
#             for i in range(idx, len(words)):
#                 if words[i] in ["daily", "historical", "trend"]:
#                     break
#                 category_words.append(words[i])
#             return " ".join(category_words).capitalize()
#     except IndexError:
#         pass
#     return None

# # Retrieve and generate response
# def retrieve_data(question):
#     conn = get_db_connection()
#     if not conn:
#         return "Database connection failed."
    
#     cursor = conn.cursor()
#     question_lower = question.lower()
#     question_lower = ' '.join(question_lower.split())  # Normalize spaces
#     print(f"Processing question: {question_lower}")

#     try:
#         # Question 8: Recommend products for online sales
#         if "online sales" in question_lower and ("prioritize" in question_lower or "recommend" in question_lower):
#             print("Question 8 triggered")
#             query = """
#                 SELECT brand, category, size, color, sales_qty, purchase_qty
#                 FROM sales_data
#                 WHERE purchase_qty > sales_qty
#                 ORDER BY (purchase_qty - sales_qty) DESC
#                 LIMIT 10
#             """
#             cursor.execute(query)
#             results = cursor.fetchall()
#             print(f"Query results: {len(results)} rows")
#             if not results:
#                 return "No products with excess inventory found for online sales prioritization."
#             df = pd.DataFrame(results, columns=["brand", "category", "size", "color", "sales_qty", "purchase_qty"])
#             df['inventory'] = df['purchase_qty'] - df['sales_qty']
#             return f"<h3>Products Recommended for Online Sales</h3>" + df[['brand', 'category', 'size', 'color', 'inventory']].to_html(index=False, classes="data-table")

#         # Question 1: Notify when items reach 75% and 50% sold
#         elif "reach 75% and 50% sold" in question_lower:
#             print("Question 1 triggered")
#             query = """
#                 SELECT brand, category, size, color, sales_qty, purchase_qty, created_at
#                 FROM sales_data
#                 WHERE purchase_qty > 0 AND LOWER(brand) != 'grand total'
#             """
#             cursor.execute(query)
#             results = cursor.fetchall()
#             if not results:
#                 return "No data found."
#             df = pd.DataFrame(results, columns=["brand", "category", "size", "color", "sales_qty", "purchase_qty", "created_at"])
#             df['percent_sold'] = (df['sales_qty'] / df['purchase_qty']) * 100
#             df['days_since'] = (datetime.now() - df['created_at']).dt.days
#             df['days_to_sell_out'] = df.apply(lambda row: calculate_days_to_sell_out(row['sales_qty'], row['purchase_qty'], row['days_since']), axis=1)
#             filtered = df[(df['percent_sold'] >= 50) & (df['percent_sold'] <= 75)]
#             if filtered.empty:
#                 return "No items between 50% and 75% sold."
#             return filtered[['brand', 'category', 'size', 'color', 'percent_sold', 'days_to_sell_out']].to_html(index=False, classes="data-table")

#         # Question 2: Best-selling items by specific period(s)
#         elif "best-selling items" in question_lower:
#             print("Question 2 triggered")
#             periods = {"weekly": 7, "monthly": 30, "quarterly": 90}
#             requested_periods = [p for p in periods if p in question_lower]
#             if not requested_periods:
#                 return "Please specify a period (weekly, monthly, or quarterly) for best-selling items."
#             output = ""
#             for period_name in requested_periods:
#                 days = periods[period_name]
#                 query = """
#                     SELECT brand, category, size, color, SUM(sales_qty) as total_sales
#                     FROM sales_data
#                     WHERE created_at >= %s AND LOWER(brand) != 'grand total'
#                     GROUP BY brand, category, size, color
#                     ORDER BY total_sales DESC
#                     LIMIT 5
#                 """
#                 cursor.execute(query, (datetime.now() - timedelta(days=days),))
#                 results = cursor.fetchall()
#                 if results:
#                     df = pd.DataFrame(results, columns=["brand", "category", "size", "color", "total_sales"])
#                     output += f"<h3>Top 5 Best-Selling Items ({period_name.capitalize()})</h3>"
#                     output += df.to_html(index=False, classes="data-table")
#                 else:
#                     output += f"<h3>No best-selling items found for {period_name.capitalize()} period.</h3>"
#             return output if output else "No best-selling items found for the specified period(s)."

#         # Question 3: Track non-moving products
#         elif "non-moving products" in question_lower:
#             print("Question 3 triggered")
#             query = """
#                 SELECT brand, category, size, color, purchase_qty, created_at
#                 FROM sales_data
#                 WHERE sales_qty = 0 AND created_at >= %s AND LOWER(brand) != 'grand total'
#             """
#             one_month_ago = datetime.now() - timedelta(days=30)
#             cursor.execute(query, (one_month_ago,))
#             results = cursor.fetchall()
#             if not results:
#                 return "No non-moving products found."
#             df = pd.DataFrame(results, columns=["brand", "category", "size", "color", "purchase_qty", "created_at"])
#             df['age_days'] = (datetime.now() - df['created_at']).dt.days
#             return df[['brand', 'category', 'size', 'color', 'purchase_qty', 'age_days']].to_html(index=False, classes="data-table")

#         # Question 4: Identify slow-moving sizes within specific categories
#         elif "slow-moving sizes" in question_lower:
#             print("Question 4 triggered")
#             query = """
#                 SELECT brand, category, size, color, sales_qty, purchase_qty, created_at
#                 FROM sales_data
#                 WHERE LOWER(brand) != 'grand total'
#             """
#             cursor.execute(query)
#             results = cursor.fetchall()
#             if not results:
#                 return "No data found for slow-moving sizes."
#             df = pd.DataFrame(results, columns=["brand", "category", "size", "color", "sales_qty", "purchase_qty", "created_at"])
#             df['days_since'] = (datetime.now() - df['created_at']).dt.days
#             df['sales_velocity'] = df['sales_qty'] / df['days_since'].replace(0, 1)
#             category = extract_category(question)
#             if not category:
#                 df_grouped = df.groupby('size').agg({'sales_qty': 'sum', 'purchase_qty': 'sum', 'sales_velocity': 'mean'}).reset_index()
#                 df_sorted = df_grouped.sort_values(by='sales_velocity').head(5)
#                 return f"<h3>Top 5 Slow-Moving Sizes Across All Categories</h3>" + df_sorted[['size', 'sales_qty', 'purchase_qty', 'sales_velocity']].to_html(index=False, classes="data-table")
#             else:
#                 df_category = df[df['category'].str.lower() == category.lower()]
#                 if df_category.empty:
#                     available_categories = df['category'].unique().tolist()
#                     return f"No data found for category '{category}'. Available categories: {', '.join(available_categories)}"
#                 df_grouped = df_category.groupby('size').agg({'sales_qty': 'sum', 'purchase_qty': 'sum', 'sales_velocity': 'mean'}).reset_index()
#                 df_sorted = df_grouped.sort_values(by='sales_velocity').head(5)
#                 return f"<h3>Slow-Moving Sizes in {category}</h3>" + df_sorted[['size', 'sales_qty', 'purchase_qty', 'sales_velocity']].to_html(index=False, classes="data-table")

#         # Question 5: Provide insights on variances and suggest strategies
#         elif re.search(r"\b(variances|strategies)\b", question_lower):
#             print("Question 5 triggered")
#             query = """
#                 SELECT brand, category, size, color, sales_qty, purchase_qty
#                 FROM sales_data
#             """
#             cursor.execute(query)
#             results = cursor.fetchall()
#             if not results:
#                 return "No data found for variance analysis."
#             df = pd.DataFrame(results, columns=["brand", "category", "size", "color", "sales_qty", "purchase_qty"])
#             df['sales_ratio'] = df['sales_qty'] / df['purchase_qty'].replace(0, 1)
#             low_sales = df[df['sales_ratio'] < 0.5]
#             if low_sales.empty:
#                 return "No products with significant variances found."
#             strategies = "Consider the following strategies for improvement:\n<ul>"
#             strategies += "<li>Offer discounts or promotions on low-selling items.</li>"
#             strategies += "<li>Bundle low-selling items with popular products.</li>"
#             strategies += "<li>Analyze customer feedback to understand why certain items are not selling.</li>"
#             strategies += "<li>Consider discontinuing items with consistently low sales.</li></ul>"
#             insights = low_sales[['brand', 'category', 'size', 'color', 'sales_ratio']].to_html(index=False, classes="data-table")
#             return f"<h3>Products with Low Sales Relative to Purchase</h3>{insights}<br><h3>Suggested Strategies</h3><p>{strategies}</p>"

#         # Question 6: Analyze turnaround time (proxy solution)
#         elif "turnaround time for exchanges and returns" in question_lower:
#             print("Question 6 triggered")
#             query = """
#                 SELECT brand, category, size, color, sales_qty, purchase_qty, created_at
#                 FROM sales_data
#                 WHERE purchase_qty > sales_qty
#             """
#             cursor.execute(query)
#             results = cursor.fetchall()
#             if not results:
#                 return "No data found for turnaround analysis."
#             df = pd.DataFrame(results, columns=["brand", "category", "size", "color", "sales_qty", "purchase_qty", "created_at"])
#             df['days_since'] = (datetime.now() - df['created_at']).dt.days
#             df['unsold_qty'] = df['purchase_qty'] - df['sales_qty']
#             df_sorted = df.sort_values(by='days_since', ascending=False).head(10)
#             note = "<p>Note: No return data available. Showing items with high unsold stock and time since purchase as a proxy for potential returns/exchanges.</p>"
#             return f"<h3>Potential Turnaround Issues</h3>{df_sorted[['brand', 'category', 'size', 'color', 'unsold_qty', 'days_since']].to_html(index=False, classes='data-table')}<br>{note}"

#         # Question 7: Reports on rejected goods and returns (proxy solution)
#         elif "reports on rejected goods and returns" in question_lower:
#             print("Question 7 triggered")
#             query = """
#                 SELECT brand, category, size, color, sales_qty, purchase_qty
#                 FROM sales_data
#                 WHERE sales_qty = 0 AND purchase_qty > 0
#             """
#             cursor.execute(query)
#             results = cursor.fetchall()
#             if not results:
#                 return "No potential rejected goods found."
#             df = pd.DataFrame(results, columns=["brand", "category", "size", "color", "sales_qty", "purchase_qty"])
#             note = "<p>Note: No rejection data available. Showing non-moving items as potential rejections for vendor feedback.</p>"
#             return f"<h3>Potential Rejected Goods</h3>{df[['brand', 'category', 'size', 'color', 'purchase_qty']].to_html(index=False, classes='data-table')}<br>{note}"

#         # Question 9: Identify unique products
#         elif "unique products" in question_lower:
#             print("Question 9 triggered")
#             query = """
#                 SELECT DISTINCT brand, category, size, color
#                 FROM sales_data
#                 LIMIT 10
#             """
#             cursor.execute(query)
#             results = cursor.fetchall()
#             if not results:
#                 return "No unique products found."
#             df = pd.DataFrame(results, columns=["brand", "category", "size", "color"])
#             return df.to_html(index=False, classes="data-table")

#         # Question 10: Identify products contributing to X% of sales (dynamic percentage)
#         elif "products contributing to" in question_lower and "% of sales" in question_lower:
#             match = re.search(r'contributing to (\d+)% of sales', question_lower)
#             if match:
#                 percentage = int(match.group(1))
#             else:
#                 return "Please specify a percentage of sales in your query (e.g., 'products contributing to 80% of sales')."
#             query = """
#                 SELECT brand, category, size, color, SUM(sales_qty) as total_sales
#                 FROM sales_data
#                 WHERE LOWER(brand) != 'grand total'
#                 GROUP BY brand, category, size, color
#                 ORDER BY total_sales DESC
#             """
#             cursor.execute(query)
#             results = cursor.fetchall()
#             if not results:
#                 return "No sales data found."
#             df = pd.DataFrame(results, columns=["brand", "category", "size", "color", "total_sales"])
#             total_sales = df['total_sales'].sum()
#             df['cumulative_sales'] = df['total_sales'].cumsum()
#             df['cumulative_percent'] = df['cumulative_sales'] / total_sales * 100
#             if not df.empty:
#                 k = (df['cumulative_percent'] >= percentage).idxmax()
#                 if df['cumulative_percent'].iloc[k] >= percentage:
#                     top_products = df.iloc[:k+1]
#                 else:
#                     top_products = df
#             else:
#                 top_products = pd.DataFrame()
#             if top_products.empty:
#                 return f"No products found contributing to {percentage}% of sales."
#             return f"<h3>Products contributing to at least {percentage}% of sales</h3>" + top_products[['brand', 'category', 'size', 'color', 'total_sales']].to_html(index=False, classes="data-table")

#         # Question 11: Suggest strategies to reduce inventory of low-performing items
#         elif re.search(r"\b(reduce inventory)\b.*\b(low-performing|strategies)\b", question_lower) or re.search(r"\b(strategies)\b.*\b(reduce inventory)\b", question_lower):
#             print("Question 11 triggered")
#             query = """
#                 SELECT brand, category, size, color, sales_qty, purchase_qty
#                 FROM sales_data
#                 WHERE sales_qty < 0.1 * purchase_qty
#                 ORDER BY purchase_qty DESC
#                 LIMIT 10
#             """
#             cursor.execute(query)
#             results = cursor.fetchall()
#             if not results:
#                 return "No low-performing items found."
#             df = pd.DataFrame(results, columns=["brand", "category", "size", "color", "sales_qty", "purchase_qty"])
#             strategies = "Strategies to reduce inventory of low-performing items:\n<ul>"
#             strategies += "<li>Implement clearance sales or discounts.</li>"
#             strategies += "<li>Use low-performing items in promotional bundles.</li>"
#             strategies += "<li>Donate or liquidate excess stock.</li>"
#             strategies += "<li>Adjust future purchasing based on sales data.</li></ul>"
#             insights = df.to_html(index=False, classes="data-table")
#             return f"<h3>Low-Performing Items</h3>{insights}<br><h3>Suggested Strategies</h3><p>{strategies}</p>"

#         # Default response
#         else:
#             print("Default response triggered")
#             return "Please ask a question I can answer with sales data."

#     except Exception as e:
#         print(f"Exception: {e}")
#         return f"Error: {e}"
#     finally:
#         cursor.close()
#         conn.close()

# # Flask app
# app = Flask(__name__)

# # Serve the chat interface
# @app.route("/", methods=["GET"])
# def index():
#     return render_template("other.html")

# # Handle chat requests from the UI
# @app.route("/chat", methods=["POST"])
# def chat():
#     data = request.get_json()
#     question = data.get("question")
#     if not question:
#         return jsonify({"text": "Please provide a question."})
#     answer = retrieve_data(question)
#     return jsonify({"text": answer})

# if __name__ == "__main__":
#     app.run(debug=True)
  #OG one



import pandas as pd
from datetime import datetime, timedelta
import re

# Helper function for sell-out days with zero handling
def calculate_days_to_sell_out(sales_qty, purchase_qty, days_since):
    if sales_qty == 0 or purchase_qty == 0 or days_since == 0:
        return "N/A"
    remaining = purchase_qty - sales_qty
    if remaining <= 0:
        return "Sold out"
    daily_rate = sales_qty / days_since
    if daily_rate <= 0:
        return "N/A"
    return round(remaining / daily_rate)

# Helper function to extract category from question
def extract_category(question):
    words = question.lower().split()
    try:
        if "in" in words:
            idx = words.index("in") + 1
            category_words = []
            for i in range(idx, len(words)):
                if words[i] in ["daily", "historical", "trend"]:
                    break
                category_words.append(words[i])
            return " ".join(category_words).capitalize()
        elif "for" in words:
            idx = words.index("for") + 1
            category_words = []
            for i in range(idx, len(words)):
                if words[i] in ["daily", "historical", "trend"]:
                    break
                category_words.append(words[i])
            return " ".join(category_words).capitalize()
    except IndexError:
        pass
    return None

# Retrieve and generate response for chatbot
def retrieve_data(question, logger):
    # Note: get_db_connection will be passed from data.py
    from data import get_db_connection  # Import here to avoid circular imports
    conn = get_db_connection()
    if not conn:
        return "Database connection failed."
    
    cursor = conn.cursor()
    question_lower = ' '.join(question.lower().split())  # Normalize spaces
    logger.info(f"Processing chatbot question: {question_lower}")

    try:
        # Question 8: Recommend products for online sales
        if "online sales" in question_lower and ("prioritize" in question_lower or "recommend" in question_lower):
            logger.info("Question 8 triggered")
            query = """
                SELECT brand, category, size, color, sales_qty, purchase_qty
                FROM sales_data
                WHERE purchase_qty > sales_qty
                ORDER BY (purchase_qty - sales_qty) DESC
                LIMIT 10
            """
            cursor.execute(query)
            results = cursor.fetchall()
            logger.info(f"Query results: {len(results)} rows")
            if not results:
                return "No products with excess inventory found for online sales prioritization."
            df = pd.DataFrame(results, columns=["brand", "category", "size", "color", "sales_qty", "purchase_qty"])
            df['inventory'] = df['purchase_qty'] - df['sales_qty']
            return f"<h3>Products Recommended for Online Sales</h3>" + df[['brand', 'category', 'size', 'color', 'inventory']].to_html(index=False, classes="data-table")

        # Question 1: Notify when items reach 75% and 50% sold
        elif "reach 75% and 50% sold" in question_lower:
            logger.info("Question 1 triggered")
            query = """
                SELECT brand, category, size, color, sales_qty, purchase_qty, created_at
                FROM sales_data
                WHERE purchase_qty > 0 AND LOWER(brand) != 'grand total'
            """
            cursor.execute(query)
            results = cursor.fetchall()
            if not results:
                return "No data found."
            df = pd.DataFrame(results, columns=["brand", "category", "size", "color", "sales_qty", "purchase_qty", "created_at"])
            df['created_at'] = pd.to_datetime(df['created_at'])
            df['days_since'] = (datetime.now() - df['created_at']).dt.days
            df['percent_sold'] = (df['sales_qty'] / df['purchase_qty']) * 100
            df['days_to_sell_out'] = df.apply(lambda row: calculate_days_to_sell_out(row['sales_qty'], row['purchase_qty'], row['days_since']), axis=1)
            filtered = df[(df['percent_sold'] >= 50) & (df['percent_sold'] <= 75)]
            if filtered.empty:
                return "No items between 50% and 75% sold."
            return filtered[['brand', 'category', 'size', 'color', 'percent_sold', 'days_to_sell_out']].to_html(index=False, classes="data-table")

        # Question 2: Best-selling items by specific period(s)
        elif "best-selling items" in question_lower:
            logger.info("Question 2 triggered")
            periods = {"weekly": 7, "monthly": 30, "quarterly": 90}
            requested_periods = [p for p in periods if p in question_lower]
            if not requested_periods:
                return "Please specify a period (weekly, monthly, or quarterly) for best-selling items."
            output = ""
            for period_name in requested_periods:
                days = periods[period_name]
                query = """
                    SELECT brand, category, size, color, SUM(sales_qty) as total_sales
                    FROM sales_data
                    WHERE created_at >= %s AND LOWER(brand) != 'grand total'
                    GROUP BY brand, category, size, color
                    ORDER BY total_sales DESC
                    LIMIT 5
                """
                cursor.execute(query, (datetime.now() - timedelta(days=days),))
                results = cursor.fetchall()
                if results:
                    df = pd.DataFrame(results, columns=["brand", "category", "size", "color", "total_sales"])
                    output += f"<h3>Top 5 Best-Selling Items ({period_name.capitalize()})</h3>"
                    output += df.to_html(index=False, classes="data-table")
                else:
                    output += f"<h3>No best-selling items found for {period_name.capitalize()} period.</h3>"
            return output if output else "No best-selling items found for the specified period(s)."

        # Question 3: Track non-moving products
        elif "non-moving products" in question_lower:
            logger.info("Question 3 triggered")
            query = """
                SELECT brand, category, size, color, purchase_qty, created_at
                FROM sales_data
                WHERE sales_qty = 0 AND created_at >= %s AND LOWER(brand) != 'grand total'
            """
            one_month_ago = datetime.now() - timedelta(days=30)
            cursor.execute(query, (one_month_ago,))
            results = cursor.fetchall()
            if not results:
                return "No non-moving products found."
            df = pd.DataFrame(results, columns=["brand", "category", "size", "color", "purchase_qty", "created_at"])
            df['created_at'] = pd.to_datetime(df['created_at'])
            df['age_days'] = (datetime.now() - df['created_at']).dt.days
            return df[['brand', 'category', 'size', 'color', 'purchase_qty', 'age_days']].to_html(index=False, classes="data-table")

        # Question 4: Identify slow-moving sizes within specific categories
        elif "slow-moving sizes" in question_lower:
            logger.info("Question 4 triggered")
            query = """
                SELECT brand, category, size, color, sales_qty, purchase_qty, created_at
                FROM sales_data
                WHERE LOWER(brand) != 'grand total'
            """
            cursor.execute(query)
            results = cursor.fetchall()
            if not results:
                return "No data found for slow-moving sizes."
            df = pd.DataFrame(results, columns=["brand", "category", "size", "color", "sales_qty", "purchase_qty", "created_at"])
            df['created_at'] = pd.to_datetime(df['created_at'])
            df['days_since'] = (datetime.now() - df['created_at']).dt.days
            df['sales_velocity'] = df['sales_qty'] / df['days_since'].replace(0, 1)
            category = extract_category(question)
            if not category:
                df_grouped = df.groupby('size').agg({'sales_qty': 'sum', 'purchase_qty': 'sum', 'sales_velocity': 'mean'}).reset_index()
                df_sorted = df_grouped.sort_values(by='sales_velocity').head(5)
                return f"<h3>Top 5 Slow-Moving Sizes Across All Categories</h3>" + df_sorted[['size', 'sales_qty', 'purchase_qty', 'sales_velocity']].to_html(index=False, classes="data-table")
            else:
                df_category = df[df['category'].str.lower() == category.lower()]
                if df_category.empty:
                    available_categories = df['category'].unique().tolist()
                    return f"No data found for category '{category}'. Available categories: {', '.join(available_categories)}"
                df_grouped = df_category.groupby('size').agg({'sales_qty': 'sum', 'purchase_qty': 'sum', 'sales_velocity': 'mean'}).reset_index()
                df_sorted = df_grouped.sort_values(by='sales_velocity').head(5)
                return f"<h3>Slow-Moving Sizes in {category}</h3>" + df_sorted[['size', 'sales_qty', 'purchase_qty', 'sales_velocity']].to_html(index=False, classes="data-table")

        # Question 5: Provide insights on variances and suggest strategies
        elif re.search(r"\b(variances|strategies)\b", question_lower):
            logger.info("Question 5 triggered")
            query = """
                SELECT brand, category, size, color, sales_qty, purchase_qty
                FROM sales_data
            """
            cursor.execute(query)
            results = cursor.fetchall()
            if not results:
                return "No data found for variance analysis."
            df = pd.DataFrame(results, columns=["brand", "category", "size", "color", "sales_qty", "purchase_qty"])
            df['sales_ratio'] = df['sales_qty'] / df['purchase_qty'].replace(0, 1)
            low_sales = df[df['sales_ratio'] < 0.5]
            if low_sales.empty:
                return "No products with significant variances found."
            strategies = "Consider the following strategies for improvement:\n<ul>"
            strategies += "<li>Offer discounts or promotions on low-selling items.</li>"
            strategies += "<li>Bundle low-selling items with popular products.</li>"
            strategies += "<li>Analyze customer feedback to understand why certain items are not selling.</li>"
            strategies += "<li>Consider discontinuing items with consistently low sales.</li></ul>"
            insights = low_sales[['brand', 'category', 'size', 'color', 'sales_ratio']].to_html(index=False, classes="data-table")
            return f"<h3>Products with Low Sales Relative to Purchase</h3>{insights}<br><h3>Suggested Strategies</h3><p>{strategies}</p>"

        # Question 6: Analyze turnaround time (proxy solution)
        elif "turnaround time for exchanges and returns" in question_lower:
            logger.info("Question 6 triggered")
            query = """
                SELECT brand, category, size, color, sales_qty, purchase_qty, created_at
                FROM sales_data
                WHERE purchase_qty > sales_qty
            """
            cursor.execute(query)
            results = cursor.fetchall()
            if not results:
                return "No data found for turnaround analysis."
            df = pd.DataFrame(results, columns=["brand", "category", "size", "color", "sales_qty", "purchase_qty", "created_at"])
            df['created_at'] = pd.to_datetime(df['created_at'])
            df['days_since'] = (datetime.now() - df['created_at']).dt.days
            df['unsold_qty'] = df['purchase_qty'] - df['sales_qty']
            df_sorted = df.sort_values(by='days_since', ascending=False).head(10)
            note = "<p>Note: No return data available. Showing items with high unsold stock and time since purchase as a proxy for potential returns/exchanges.</p>"
            return f"<h3>Potential Turnaround Issues</h3>{df_sorted[['brand', 'category', 'size', 'color', 'unsold_qty', 'days_since']].to_html(index=False, classes='data-table')}<br>{note}"

        # Question 7: Reports on rejected goods and returns (proxy solution)
        elif "reports on rejected goods and returns" in question_lower:
            logger.info("Question 7 triggered")
            query = """
                SELECT brand, category, size, color, sales_qty, purchase_qty
                FROM sales_data
                WHERE sales_qty = 0 AND purchase_qty > 0
            """
            cursor.execute(query)
            results = cursor.fetchall()
            if not results:
                return "No potential rejected goods found."
            df = pd.DataFrame(results, columns=["brand", "category", "size", "color", "sales_qty", "purchase_qty"])
            note = "<p>Note: No rejection data available. Showing non-moving items as potential rejections for vendor feedback.</p>"
            return f"<h3>Potential Rejected Goods</h3>{df[['brand', 'category', 'size', 'color', 'purchase_qty']].to_html(index=False, classes='data-table')}<br>{note}"

        # Question 9: Identify unique products
        elif "unique products" in question_lower:
            logger.info("Question 9 triggered")
            query = """
                SELECT DISTINCT brand, category, size, color
                FROM sales_data
                LIMIT 10
            """
            cursor.execute(query)
            results = cursor.fetchall()
            if not results:
                return "No unique products found."
            df = pd.DataFrame(results, columns=["brand", "category", "size", "color"])
            return df.to_html(index=False, classes="data-table")

        # Question 10: Identify products contributing to X% of sales (dynamic percentage)
        elif "products contributing to" in question_lower and "% of sales" in question_lower:
            match = re.search(r'contributing to (\d+)% of sales', question_lower)
            if match:
                percentage = int(match.group(1))
            else:
                return "Please specify a percentage of sales in your query (e.g., 'products contributing to 80% of sales')."
            query = """
                SELECT brand, category, size, color, SUM(sales_qty) as total_sales
                FROM sales_data
                WHERE LOWER(brand) != 'grand total'
                GROUP BY brand, category, size, color
                ORDER BY total_sales DESC
            """
            cursor.execute(query)
            results = cursor.fetchall()
            if not results:
                return "No sales data found."
            df = pd.DataFrame(results, columns=["brand", "category", "size", "color", "total_sales"])
            total_sales = df['total_sales'].sum()
            df['cumulative_sales'] = df['total_sales'].cumsum()
            df['cumulative_percent'] = df['cumulative_sales'] / total_sales * 100
            if not df.empty:
                k = (df['cumulative_percent'] >= percentage).idxmax()
                if df['cumulative_percent'].iloc[k] >= percentage:
                    top_products = df.iloc[:k+1]
                else:
                    top_products = df
            else:
                top_products = pd.DataFrame()
            if top_products.empty:
                return f"No products found contributing to {percentage}% of sales."
            return f"<h3>Products contributing to at least {percentage}% of sales</h3>" + top_products[['brand', 'category', 'size', 'color', 'total_sales']].to_html(index=False, classes="data-table")

        # Question 11: Suggest strategies to reduce inventory of low-performing items
        elif re.search(r"\b(reduce inventory)\b.*\b(low-performing|strategies)\b", question_lower) or re.search(r"\b(strategies)\b.*\b(reduce inventory)\b", question_lower):
            logger.info("Question 11 triggered")
            query = """
                SELECT brand, category, size, color, sales_qty, purchase_qty
                FROM sales_data
                WHERE sales_qty < 0.1 * purchase_qty
                ORDER BY purchase_qty DESC
                LIMIT 10
            """
            cursor.execute(query)
            results = cursor.fetchall()
            if not results:
                return "No low-performing items found."
            df = pd.DataFrame(results, columns=["brand", "category", "size", "color", "sales_qty", "purchase_qty"])
            strategies = "Strategies to reduce inventory of low-performing items:\n<ul>"
            strategies += "<li>Implement clearance sales or discounts.</li>"
            strategies += "<li>Use low-performing items in promotional bundles.</li>"
            strategies += "<li>Donate or liquidate excess stock.</li>"
            strategies += "<li>Adjust future purchasing based on sales data.</li></ul>"
            insights = df.to_html(index=False, classes="data-table")
            return f"<h3>Low-Performing Items</h3>{insights}<br><h3>Suggested Strategies</h3><p>{strategies}</p>"

        # Default response
        else:
            logger.info("Default response triggered")
            return "Please ask a question I can answer with sales data."

    except Exception as e:
        logger.error(f"Exception in retrieve_data: {e}")
        return f"Error: {e}"
    finally:
        cursor.close()
        conn.close()

# Chatbot route handler (to be registered in data.py)
def chat():
    from flask import request, jsonify
    from data import FlaskLogger  # Import FlaskLogger from data.py
    log_output = FlaskLogger()
    data = request.get_json(silent=True)
    if data is None:
        log_output.error("Received non-JSON request")
        return jsonify({"text": "Invalid request format. Please send JSON data.", "logs": log_output.get_logs()}), 400
    question = data.get("question", "")
    log_output.info(f"Received chatbot question: {question}")
    if not question:
        log_output.error("No question provided")
        return jsonify({"text": "Please provide a question.", "logs": log_output.get_logs()}), 400
    answer = retrieve_data(question, log_output)
    return jsonify({"text": answer, "logs": log_output.get_logs()})
    