import pandas as pd
import os


class BOM:
    """BOM (Bill of Materials) manager using pandas DataFrame for storage.
    Each part is represented as a row in the DataFrame with
    columns for part_id, part_name, and qty. The BOM class 
    provides methods to add, edit, remove, and retrieve parts, 
    as well as print the BOM and save/load it from a CSV file.
    """

    def __init__(self):
        """ Initialize an empty BOM with a DataFrame to store parts. The DataFrame has columns for part_id, part_name, and qty.
        """
        self.df = pd.DataFrame(columns=[
            "part_id",
            "part_name",
            "qty"
        ])

        self.output_dir: str = None

    def _resolve_mask(self, part_id: str = None, part_name: str = None) -> pd.Series:
        """ Resolve a boolean mask for the DataFrame based on part_id or part_name.   

        Args:
            part_id (str, optional): The ID of the part to resolve. Defaults to None. 
            part_name (str, optional): The name of the part to resolve. Defaults to None.

        Raises:
            ValueError: If neither part_id nor part_name is provided.

        Returns:
            pd.Series: A boolean mask for the DataFrame rows that match the given part_id or part_name.
        """
        
        if part_id is None and part_name is None:
            raise ValueError("Provide part_id or part_name")

        if part_id is not None:
            return self.df["part_id"] == part_id

        if part_name is not None:
            return self.df["part_name"] == part_name

    def _ensure_unique(self, part_id: str, part_name: str) -> None:
        """ Check that the given part_id and part_name are unique in the DataFrame. Raises a ValueError if either the part_id or part_name already exists in the DataFrame.

        Args:
            part_id (str): The ID of the part to check for uniqueness.
            part_name (str): The name of the part to check for uniqueness.

        Raises:
            ValueError: If the part_id already exists in the DataFrame.
            ValueError: If the part_name already exists in the DataFrame.
        """

        if part_id in self.df["part_id"].values:
            raise ValueError(f"Duplicate part_id: {part_id}")

        if part_name in self.df["part_name"].values:
            raise ValueError(f"Duplicate part_name: {part_name}")

    def add_part(self, part_id: str, part_name: str, qty: int) -> None:
        """ Add a part to the BOM. If a part with the same part_id or part_name already exists, its quantity will be updated by adding the new quantity. If the part is new, it will be added to the DataFrame. The method ensures that part_id and part_name are unique for new parts.

        Args:
            part_id (str): The ID of the part to add.
            part_name (str): The name of the part to add.
            qty (int): The quantity of the part to add.

        Raises:
            ValueError: If qty is less than or equal to 0.
        """

        if qty <= 0:
            raise ValueError("qty must be > 0")

        # try match by id first
        mask_id = self.df["part_id"] == part_id
        mask_name = self.df["part_name"] == part_name

        if mask_id.any():
            self.df.loc[mask_id, "qty"] += qty
            return

        if mask_name.any():
            self.df.loc[mask_name, "qty"] += qty
            return

        # new part → enforce uniqueness
        self._ensure_unique(part_id, part_name)

        self.df = pd.concat([
            self.df,
            pd.DataFrame([{
                "part_id": part_id,
                "part_name": part_name,
                "qty": qty
            }])
        ], ignore_index=True)

    def edit_part(self, part_id: str = None, part_name: str = None, new_name: str = None, new_qty: int = None) -> None:
        """ Edit a part in the BOM. The part to edit can be identified by either part_id or part_name. The method allows updating the part's name and/or quantity. If new_name is provided, it checks for uniqueness before updating. If new_qty is provided, it must be non-negative.

        Args:
            part_id (str, optional): The ID of the part to edit. Defaults to None.
            part_name (str, optional): The name of the part to edit. Defaults to None.
            new_name (str, optional): The new name for the part. Defaults to None.
            new_qty (int, optional): The new quantity for the part. Defaults to None.

        Raises:
            ValueError: If the part to edit is not found.
            ValueError: If the new name already exists in the DataFrame.
            ValueError: If the new quantity is negative.
        """

        mask = self._resolve_mask(part_id, part_name)

        if not mask.any():
            raise ValueError("Part not found")

        if new_name is not None:
            if new_name in self.df["part_name"].values:
                raise ValueError(f"Duplicate part_name: {new_name}")
            self.df.loc[mask, "part_name"] = new_name

        if new_qty is not None:
            if new_qty < 0:
                raise ValueError("qty cannot be negative")
            self.df.loc[mask, "qty"] = new_qty

    def remove_part(self, part_id: str = None, part_name: str = None) -> None:
        """ Remove a part from the BOM. The part to remove can be identified by either part_id or part_name. If the part is found, it will be removed from the DataFrame. 

        Args:
            part_id (str, optional): The part to remove can be identified by either part_id or part_name. Defaults to None.
            part_name (str, optional): The name of the part to remove. Defaults to None.

        Raises:
            ValueError: If the part to remove is not found.
        """
        mask = self._resolve_mask(part_id, part_name)

        if not mask.any():
            raise ValueError("Part not found")

        self.df = self.df[~mask].reset_index(drop=True)

    def get_part(self, part_id: str = None, part_name: str = None) -> dict:
        """ Get a part from the BOM. The part to get can be identified by either part_id or part_name. 
        If the part is found, its details will be returned as a dictionary.

        Args:
            part_id (str, optional): The part to get can be identified by either part_id or part_name. Defaults to None.
            part_name (str, optional): The name of the part to get. Defaults to None

        Raises:
            ValueError: If the part to get is not found.

        Returns:
            dict: A dictionary containing the details of the part (part_id, part_name, qty) if found.
        """
        mask = self._resolve_mask(part_id, part_name)

        if not mask.any():
            raise ValueError("Part not found")

        return self.df[mask].iloc[0].to_dict()
    
    def __add__(self, other: "BOM") -> "BOM":
        """ Add another BOM to this BOM. The parts from the other BOM will be added to this BOM. 
        If a part with the same part_id or part_name already exists in this BOM, 
        their quantities will be summed. If a part from the other BOM does not exist in this BOM, 
        it will be added as a new part. The method returns a new BOM instance with the combined parts. 

        Args:
            other (BOM): _description_

        Raises:
            TypeError: _description_

        Returns:
            BOM: _description_
        """
        if not isinstance(other, BOM):
            raise TypeError("Can only add BOM with BOM")

        result = BOM()

        # copy self
        result.df = self.df.copy()

        # merge other
        for _, row in other.df.iterrows():
            result.add_part(
                row["part_id"],
                row["part_name"],
                int(row["qty"])
            )

        return result

    def print_list(self) -> None:
        """ Print the BOM as a formatted table. If the BOM is empty, it will print a message indicating that the BOM is empty. Otherwise, it will print the DataFrame containing the parts without the index.
        """
        if self.df.empty:
            print("BOM is empty")
        else:
            print(self.df.to_string(index=False))

    def save_csv(self, output_dir: str, filename: str) -> None:
        """ Save the BOM to a CSV file at the specified filepath. The CSV file will contain the columns part_id, part_name, and qty, and will not include the DataFrame index.

        Args:
            output_dir (str): The directory where the CSV file will be saved.
            filename (str): The name of the CSV file.
        """

        self.output_dir: str = (
            os.path.abspath(output_dir)
            if output_dir
            else os.path.join(os.getcwd(), "diagram_renders")
        )
        os.makedirs(self.output_dir, exist_ok=True)

        path: str = os.path.join(self.output_dir, filename)
        self.df.to_csv(path, index=False)

        print(f"CSV saved: {path}")

    def load_csv(self, filepath: str) -> None:
        """ Load the BOM from a CSV file at the specified filepath. The CSV file should contain the columns part_id, part_name, and qty. The loaded data will replace the current contents of the BOM. 

        Args:
            filepath (str): The filepath from which the CSV file will be loaded.
        """
        self.df = pd.read_csv(filepath)