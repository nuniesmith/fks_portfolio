"""
Database storage for historical data
Uses SQLite for development, can be extended to PostgreSQL
"""
from typing import List, Optional, Dict
from datetime import datetime
import sqlite3
import pandas as pd
from pathlib import Path
from loguru import logger


class DataStorage:
    """SQLite storage for historical price data"""
    
    def __init__(self, db_path: str = "data/historical/portfolio.db"):
        """
        Initialize storage
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.logger = logger.bind(component="DataStorage")
        self._init_db()
    
    def _init_db(self):
        """Initialize database schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create prices table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS prices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                date TIMESTAMP NOT NULL,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                volume REAL,
                adapter TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(symbol, date, adapter)
            )
        """)
        
        # Create index for faster queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_symbol_date 
            ON prices(symbol, date)
        """)
        
        conn.commit()
        conn.close()
        self.logger.info(f"Database initialized at {self.db_path}")
    
    def store_prices(
        self,
        symbol: str,
        prices_df: pd.DataFrame,
        adapter: str = "unknown"
    ):
        """
        Store historical prices
        
        Args:
            symbol: Asset symbol
            prices_df: DataFrame with columns: date, open, high, low, close, volume
            adapter: Adapter name
        """
        if prices_df.empty:
            return
        
        conn = sqlite3.connect(self.db_path)
        
        try:
            # Prepare data
            prices_df = prices_df.copy()
            prices_df["symbol"] = symbol
            prices_df["adapter"] = adapter
            
            # Ensure date column exists and is datetime
            if "date" not in prices_df.columns:
                self.logger.error("DataFrame missing 'date' column")
                return
            
            # Manual upsert (SQLite doesn't support method parameter in to_sql properly)
            cursor = conn.cursor()
            for _, row in prices_df.iterrows():
                # Convert date to string if it's a pandas Timestamp
                date_value = row['date']
                if hasattr(date_value, 'strftime'):
                    date_value = date_value.strftime('%Y-%m-%d')
                elif hasattr(date_value, 'isoformat'):
                    date_value = date_value.isoformat()
                
                cursor.execute("""
                    INSERT OR REPLACE INTO prices 
                    (symbol, date, open, high, low, close, volume, adapter)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    symbol,
                    date_value,
                    float(row['open']),
                    float(row['high']),
                    float(row['low']),
                    float(row['close']),
                    float(row['volume']),
                    adapter
                ))
            
            conn.commit()
            self.logger.info(f"Stored {len(prices_df)} price records for {symbol}")
        except Exception as e:
            self.logger.error(f"Error storing prices for {symbol}: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    
    def get_prices(
        self,
        symbol: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        adapter: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Retrieve historical prices
        
        Args:
            symbol: Asset symbol
            start_date: Optional start date
            end_date: Optional end date
            adapter: Optional adapter filter
        
        Returns:
            DataFrame with price data
        """
        conn = sqlite3.connect(self.db_path)
        
        try:
            query = "SELECT date, open, high, low, close, volume FROM prices WHERE symbol = ?"
            params = [symbol]
            
            if adapter:
                query += " AND adapter = ?"
                params.append(adapter)
            
            if start_date:
                query += " AND date >= ?"
                params.append(start_date)
            
            if end_date:
                query += " AND date <= ?"
                params.append(end_date)
            
            query += " ORDER BY date"
            
            df = pd.read_sql_query(query, conn, params=params, parse_dates=["date"])
            return df
        except Exception as e:
            self.logger.error(f"Error retrieving prices for {symbol}: {e}")
            return pd.DataFrame()
        finally:
            conn.close()
    
    def get_latest_price(self, symbol: str, adapter: Optional[str] = None) -> Optional[float]:
        """
        Get latest price for symbol
        
        Args:
            symbol: Asset symbol
            adapter: Optional adapter filter
        
        Returns:
            Latest close price or None
        """
        conn = sqlite3.connect(self.db_path)
        
        try:
            query = "SELECT close FROM prices WHERE symbol = ?"
            params = [symbol]
            
            if adapter:
                query += " AND adapter = ?"
                params.append(adapter)
            
            query += " ORDER BY date DESC LIMIT 1"
            
            cursor = conn.cursor()
            cursor.execute(query, params)
            result = cursor.fetchone()
            
            return float(result[0]) if result else None
        except Exception as e:
            self.logger.error(f"Error retrieving latest price for {symbol}: {e}")
            return None
        finally:
            conn.close()
    
    def get_symbols(self) -> List[str]:
        """Get list of all symbols in database"""
        conn = sqlite3.connect(self.db_path)
        
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT symbol FROM prices")
            results = cursor.fetchall()
            return [row[0] for row in results]
        except Exception as e:
            self.logger.error(f"Error retrieving symbols: {e}")
            return []
        finally:
            conn.close()

