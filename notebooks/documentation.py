import marimo

__generated_with = "0.23.5"
app = marimo.App()


@app.cell
def _():
    import gaussianfft

    return (gaussianfft,)


@app.cell
def _(gaussianfft):
    dir(gaussianfft)
    return


@app.cell
def _(gaussianfft):
    help(gaussianfft.variogram)
    return


@app.cell
def _(gaussianfft):
    help(gaussianfft.simulate)
    return


@app.cell
def _(gaussianfft):
    help(gaussianfft.simulation_size)
    return


if __name__ == "__main__":
    app.run()
