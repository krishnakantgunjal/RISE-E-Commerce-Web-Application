# 🚀 Collection Browsing & Filtering Update

I have implemented the filtering, sorting, and collection browsing features as requested.

## 1. Shop by Collection (Home Page) ✨
*   Added a new **"Shop by Collection"** section to the Home page.
*   Displays all 7 collections (Rise Air, Rise Dark, etc.) as **visual cards**.
*   Each card features a dynamic background (using the first product image) and a premium hover effect.
*   Clicking a collection takes the user directly to the pre-filtered product list.

## 2. Advanced Filtering & Sorting (Product List) 🔍
*   **Filter by Collection:** Updated the main filter dropdown to "All Collections" to allow filtering by specific series (Rise Air, Rise Marvel, etc.).
*   **Filter by Price:** Users can filter by ranges (Under ₹1,000, ₹1k-3k, etc.).
*   **Sorting:** Full sorting options enabled:
    *   Newest Products (Default)
    *   Price: Low to High
    *   Price: High to Low
    *   Name: A-Z
*   **Integration:** Filters and Sorting work together seamlessly. You can sort a specific collection by price, for example.

## 3. Implementation Details 🛠️
*   **Backend:** `store/views.py` passes all categories to the home page context.
*   **Frontend:** `home.html` updated with a responsive CSS grid layout for collections. `products_list.html` updated to reflect "Collection" terminology.
*   **UX:** Preserved URL parameters to ensure sorting applied to a filtered view does not reset the filter.

Your store now offers a premium browsing experience centered around your diverse collections! 👟🔥
