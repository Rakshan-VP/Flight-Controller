import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# Locate the file
base_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(base_dir, 'sensor_data_09_02_2026.csv')

if not os.path.exists(file_path):
    print("Error: CSV file not found")
else:
    df = pd.read_csv(file_path)
    samples = np.arange(len(df))
    time = np.linspace(0, 15.5, len(df))

    # Error Calculations
    comp_error = np.abs(df['roll_xsens'] - df['roll_comp'])
    madgwick_error = np.abs(df['roll_xsens'] - df['roll_madgwick'])

    # Plotting
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 12), sharex=False)
    plt.subplots_adjust(hspace=0.4)

    # Plot 1: Main Roll Comparison
    ax1.plot(samples, df['roll_xsens'], label='Xsens (Ref)', color='gray', alpha=0.5)
    ax1.plot(samples, df['roll_comp'], label='Comp Filter', color='blue', lw=2)
    ax1.plot(samples, df['roll_madgwick'], label='Madgwick', color='red', lw=2)
    ax1.set_title('Roll Comparison: Step Response & Oscillations')
    ax1.set_ylabel('Degrees')
    ax1.legend()
    ax1.grid(True)

    # Plot 2: Absolute Comp Error
    ax2.fill_between(samples, comp_error, color='blue', alpha=0.2)
    ax2.plot(samples, comp_error, color='blue', lw=1)
    ax2.set_title('Complementary Filter Absolute Error')
    ax2.set_ylabel('Error (deg)')
    ax2.grid(True)

    # Plot 3: Madgwick Error vs Time
    ax3.plot(time, madgwick_error, color='red', lw=1)
    ax3.set_title('Madgwick Error vs Time')
    ax3.set_xlabel('Time (seconds)')
    ax3.set_ylabel('Error (deg)')
    ax3.grid(True)

    # Save the plot to the base directory
    plot_path = os.path.join(base_dir, 'sensor_analysis.png')
    plt.savefig(plot_path)
    plt.show()
    print(f"Plot saved at: {plot_path}")