import streamlit as st
import gurobipy as gp
from gurobipy import GRB
import pandas as pd

st.title("Joint Production & Warehouse Planning")

# ---- Input Section ----
st.header("Input Parameters")

n_items = st.number_input("Number of items", min_value=1, value=2, max_value=10)
n_periods = st.number_input("Number of time periods", min_value=1, value=3, max_value=10)

# Generate item and period lists
items = [f"item{i+1}" for i in range(int(n_items))]
periods = list(range(1, int(n_periods) + 1))

# Production Cost
st.subheader("Production Cost")
prod_cost_data = {}
for i, item in enumerate(items):
    cols = st.columns(len(periods))
    for t, period in enumerate(periods):
        with cols[t]:
            prod_cost_data[(item, period)] = st.number_input(
                f"{item}, Period {period}",
                min_value=0,
                value=10 + i * 5,
                key=f"prod_{item}_{period}"
            )

# Setup Cost
st.subheader("Setup Cost")
setup_cost_data = {}
for i, item in enumerate(items):
    cols = st.columns(len(periods))
    for t, period in enumerate(periods):
        with cols[t]:
            setup_cost_data[(item, period)] = st.number_input(
                f"{item}, Period {period}",
                min_value=0,
                value=50 + i * 10,
                key=f"setup_{item}_{period}"
            )

# Holding Cost
st.subheader("Holding Cost")
holding_cost_data = {}
for i, item in enumerate(items):
    cols = st.columns(len(periods))
    for t, period in enumerate(periods):
        with cols[t]:
            holding_cost_data[(item, period)] = st.number_input(
                f"{item}, Period {period}",
                min_value=0,
                value=5 + i * 2,
                key=f"hold_{item}_{period}"
            )

# Demand
st.subheader("Demand")
demand_data = {}
for i, item in enumerate(items):
    cols = st.columns(len(periods))
    for t, period in enumerate(periods):
        with cols[t]:
            demand_data[(item, period)] = st.number_input(
                f"{item}, Period {period}",
                min_value=0,
                value=20 + t * 5,
                key=f"demand_{item}_{period}"
            )

# Max Production
st.subheader("Max Production Capacity")
max_prod_data = {}
for i, item in enumerate(items):
    cols = st.columns(len(periods))
    for t, period in enumerate(periods):
        with cols[t]:
            max_prod_data[(item, period)] = st.number_input(
                f"{item}, Period {period}",
                min_value=0,
                value=100,
                key=f"max_prod_{item}_{period}"
            )

# Warehouse Capacity
st.subheader("Warehouse Capacity")
warehouse_capacity = {}
cols = st.columns(len(periods))
for t, period in enumerate(periods):
    with cols[t]:
        warehouse_capacity[period] = st.number_input(
            f"Period {period}",
            min_value=0,
            value=200,
            key=f"wh_cap_{period}"
        )

# ---- Optimization ----
st.header("Run Optimization")
st.write("Click the button below to solve the model")

if st.button("Optimize Production Plan"):
    try:
        # Create progress messages
        status_placeholder = st.empty()
        status_placeholder.info("Setting up the model...")
        
        # Create model
        model = gp.Model("ProductionPlanningModel")
        
        # Create variables
        status_placeholder.info("Creating decision variables...")
        x = {}  # production quantity
        I = {}  # inventory level
        y = {}  # setup decision
        
        for i in items:
            for t in periods:
                x[i, t] = model.addVar(lb=0, name=f"x_{i}_{t}")
                I[i, t] = model.addVar(lb=0, name=f"I_{i}_{t}")
                y[i, t] = model.addVar(vtype=GRB.BINARY, name=f"y_{i}_{t}")
        
        # Update model to integrate new variables
        model.update()
        
        # Set objective function
        status_placeholder.info("Setting up objective function...")
        obj = gp.LinExpr()
        for i in items:
            for t in periods:
                obj += prod_cost_data[(i, t)] * x[i, t]
                obj += setup_cost_data[(i, t)] * y[i, t]
                obj += holding_cost_data[(i, t)] * I[i, t]
        
        model.setObjective(obj, GRB.MINIMIZE)
        
        # Add constraints
        status_placeholder.info("Adding constraints...")
        # Inventory balance
        for i in items:
            for t in periods:
                if t == 1:
                    # First period (no initial inventory)
                    model.addConstr(x[i, t] - demand_data[(i, t)] == I[i, t], 
                                   name=f"inv_balance_{i}_{t}")
                else:
                    # Subsequent periods
                    model.addConstr(I[i, t-1] + x[i, t] - demand_data[(i, t)] == I[i, t], 
                                   name=f"inv_balance_{i}_{t}")
        
        # Production capacity
        for i in items:
            for t in periods:
                model.addConstr(x[i, t] <= max_prod_data[(i, t)] * y[i, t], 
                               name=f"prod_capacity_{i}_{t}")
        
        # Warehouse capacity
        for t in periods:
            model.addConstr(sum(I[i, t] for i in items) <= warehouse_capacity[t], 
                           name=f"warehouse_cap_{t}")
        
        # Optimize
        status_placeholder.info("Solving the model... This may take a moment.")
        model.optimize()
        
        # Check results
        if model.Status == GRB.OPTIMAL:
            status_placeholder.success("Optimal solution found!")
            
            # Create tables for display
            st.header("Results")
            
            # Production Plan
            st.subheader("Production Plan")
            prod_data = []
            for i in items:
                row = {"Item": i}
                for t in periods:
                    row[f"Period {t}"] = round(x[i, t].X, 2)
                prod_data.append(row)
            st.table(pd.DataFrame(prod_data).set_index("Item"))
            
            # Inventory Levels
            # st.subheader("Inventory Levels")
            # inv_data = []
            # for i in items:
            #     row = {"Item": i}
            #     for t in periods:
            #         row[f"Period {t}"] = round(I[i, t].X, 2)
            #     inv_data.append(row)
            # st.table(pd.DataFrame(inv_data).set_index("Item"))
            
            # Setup Decisions
            # st.subheader("Setup Decisions (1 = Setup performed)")
            # setup_data = []
            # for i in items:
            #     row = {"Item": i}
            #     for t in periods:
            #         row[f"Period {t}"] = int(y[i, t].X)
            #     setup_data.append(row)
            # st.table(pd.DataFrame(setup_data).set_index("Item"))
            
            # Cost Breakdown
            st.subheader("Cost Analysis")
            prod_cost = sum(prod_cost_data[(i, t)] * x[i, t].X for i in items for t in periods)
            setup_cost = sum(setup_cost_data[(i, t)] * y[i, t].X for i in items for t in periods)
            holding_cost = sum(holding_cost_data[(i, t)] * I[i, t].X for i in items for t in periods)
            
            cost_df = pd.DataFrame({
                "Cost Component": ["Production Cost", "Setup Cost", "Holding Cost", "Total Cost"],
                "Amount": [
                    f"${prod_cost:.2f}",
                    f"${setup_cost:.2f}",
                    f"${holding_cost:.2f}",
                    f"${model.objVal:.2f}"
                ]
            })
            st.table(cost_df)
            
        elif model.Status == GRB.INFEASIBLE:
            status_placeholder.error("The model is infeasible!")
            st.write("The current set of constraints cannot be satisfied simultaneously.")
            st.write("Try increasing production capacities or warehouse capacities.")
            
        else:
            status_placeholder.warning(f"Model terminated with status: {model.Status}")
            st.write("Please check your input data and try again.")
            
    except Exception as e:
        st.error(f"An error occurred: {type(e).__name__}")
        st.error(str(e))
        import traceback
        st.code(traceback.format_exc())
        st.warning("For Gurobi-specific issues, please check your Gurobi license and installation.")